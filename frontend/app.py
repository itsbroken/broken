import zmq
import json
import logging
import sys
import os.path
from zmq.eventloop import ioloop, zmqstream
from tornado import websocket, web, ioloop, gen
from tornado.options import define, options

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from broken import utils, store

logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

zmq.eventloop.ioloop.install()

counter = 0
define("port", default=8888, help="run on the given port", type=int)


class Application(web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/websocket", MainWebSocketHandler),
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "../frontend/public/"),
            static_path=os.path.join(os.path.dirname(__file__), "../frontend/public/"),
            compress_response=True,
        )
        super(Application, self).__init__(handlers, **settings)


class MainHandler(web.RequestHandler):
    def initialize(self):
        pass

    @web.asynchronous
    def get(self):
        self.render("index.html")


class MainWebSocketHandler(websocket.WebSocketHandler):
    index = None

    @staticmethod
    def parse_message(message):
        """Parse user input"""
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            return False

        url = data.get("url")
        if not isinstance(url, str):
            return False

        opts = data.get("options")
        if not opts:
            return False

        accepted_urls = opts.get("acceptedUrls")
        if accepted_urls not in ["0", "1"]:
            return False
        limit_to_url = int(accepted_urls) == 1

        crawl_duration = opts.get("crawlDuration")
        if crawl_duration not in ["0", "1", "2"]:
            return False
        crawl_duration = (30, 60, 300)[int(crawl_duration)]

        media_types = opts.get("mediaTypes")
        if not isinstance(media_types, list):
            return False
        check_images = False
        check_videos = False
        for media_type in media_types:
            if media_type == "0":
                check_images = True
            elif media_type == "1":
                check_videos = True
            else:
                return False

        opts = {"limit_to_url": limit_to_url, "crawl_duration": crawl_duration,
                "check_images": check_images, "check_videos": check_videos}
        return url, opts

    def open(self):
        ip = self.request.remote_ip
        ua = self.request.headers["User-Agent"]
        logging.info("WebSocket opened: IP {}, User-Agent {}".format(ip, ua))

    @gen.coroutine
    def on_message(self, message):
        """Handles messages received from the websocket"""
        logging.info(message)

        parsed_message = MainWebSocketHandler.parse_message(message)
        if not parsed_message:
            logging.info("Invalid request; ignoring")
            return

        url = parsed_message[0]
        opts = parsed_message[1]

        if not utils.is_valid_url(url):
            logging.info("Invalid URL; ignoring")
            return

        global counter
        counter += 1
        self.index = counter  # Create an index for each message

        logging.info("#{} - New crawl request: {} {}".format(self.index, url, opts))

        ctx = zmq.Context.instance()

        # Subscribe to the status socket to retrieve updates from the backend
        status_socket = ctx.socket(zmq.SUB)
        status_socket.connect('tcp://127.0.0.1:5556')
        status_socket.setsockopt_string(zmq.SUBSCRIBE, str(self.index))

        status_stream = zmqstream.ZMQStream(status_socket)
        status_stream.on_recv(self.handle_reply)

        # Push to the command socket to tell the backend what to do
        s = ctx.socket(zmq.PUSH)
        s.connect('tcp://127.0.0.1:5555')
        s.send_pyobj((self.index, url, opts))

    def handle_reply(self, data):
        """Handles published updates from the backend"""
        msg = ""
        status_update = json.loads(data[0].decode('utf-8').split(',', 1)[1])
        update_type = store.Status(status_update["type"])
        update_data = status_update["data"]

        if update_type is store.Status.counts:
            msg = {"response_type": "update_counts", "counts": update_data}
        elif update_type is store.Status.broken_links:
            msg = {"response_type": "update_links", "links": update_data}
        elif update_type is store.Status.progress:
            msg = {"response_type": "status", "status": update_data}

        if msg and self.ws_connection:
            self.write_message(msg)

    def on_close(self):
        logging.info("WebSocket closed")
        # message backend to stop crawling
        if self.index:
            ctx = zmq.Context.instance()
            s = ctx.socket(zmq.PUSH)
            s.connect('tcp://127.0.0.1:5555')
            s.send_pyobj((self.index, None, None))


if __name__ == "__main__":
    options.parse_command_line()
    app = Application()
    app.listen(options.port, xheaders=True)
    ioloop.IOLoop.current().start()

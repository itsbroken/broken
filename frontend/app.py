import zmq
from zmq.eventloop import ioloop, zmqstream
from tornado import websocket, web, ioloop, gen
from tornado.options import define, options
import json
import os.path

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from broken import utils, store

import logging
import sys
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
            # cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            template_path=os.path.join(os.path.dirname(__file__), "../frontend/public/"),
            static_path=os.path.join(os.path.dirname(__file__), "../frontend/public/"),
            compress_response=True,
            # xsrf_cookies=True,
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
        for media_type in media_types:
            if media_type not in ["0", "1"]:
                return False
        media_types = [int(media_type) for media_type in media_types]

        opts = {"limit_to_url": limit_to_url, "crawl_duration": crawl_duration, "media_types": media_types}
        return url, opts

    def open(self):
        ip = self.request.remote_ip
        ua = self.request.headers["User-Agent"]
        logging.info("WebSocket opened: IP {}, User-Agent {}".format(ip, ua))

    @gen.coroutine
    def on_message(self, message):
        data = json.loads(message)
        logging.info(message)
        parsed_message = MainWebSocketHandler.parse_message(message)
        if not parsed_message:
            logging.info("Invalid request; ignoring")
        url = parsed_message[0]
        opts = parsed_message[1]
        logging.info("New crawl request: {} {}".format(url, opts))

        if utils.is_valid_url(url):
            global counter
            counter += 1
            self.index = counter

            ctx = zmq.Context.instance()

            status_socket = ctx.socket(zmq.SUB)
            status_socket.connect('tcp://127.0.0.1:5556')
            status_socket.setsockopt_string(zmq.SUBSCRIBE, str(self.index))

            status_stream = zmqstream.ZMQStream(status_socket)
            status_stream.on_recv(self.handle_reply)

            s = ctx.socket(zmq.PUSH)
            s.connect('tcp://127.0.0.1:5555')
            s.send_pyobj((self.index, url, opts))

    def handle_reply(self, data):
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

    def check_origin(self, origin):  # TODO: check origin properly
        return True


if __name__ == "__main__":
    options.parse_command_line()
    app = Application()
    app.listen(options.port, xheaders=True)
    ioloop.IOLoop.current().start()

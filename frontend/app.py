import zmq
from zmq.eventloop import ioloop, zmqstream
from tornado import websocket, web, ioloop, gen
from tornado.options import define, options
import json
from broken import utils, store
import os.path

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
    def open(self):
        print("WebSocket opened")

    @gen.coroutine
    def on_message(self, message):
        data = json.loads(message)
        url = data["url"]
        print(url)

        if utils.is_valid_url(url):
            global counter
            counter += 1
            index = counter

            ctx = zmq.Context.instance()
            s = ctx.socket(zmq.REQ)
            s.connect('tcp://127.0.0.1:5555')
            s.send_pyobj((index, url))

            status_socket = ctx.socket(zmq.SUB)
            status_socket.connect('tcp://127.0.0.1:5556')
            status_socket.setsockopt_string(zmq.SUBSCRIBE, str(index))

            self.write_message({"response_type": "status", "status": "crawling"})
            self.status_stream = zmqstream.ZMQStream(status_socket)
            self.status_stream.on_recv_stream(self.handle_reply)
            self.command_stream = zmqstream.ZMQStream(s)
            self.command_stream.on_recv_stream(self.handle_reply)

    def handle_reply(self, stream, data):
        msg = ""
        if stream == self.status_stream:
            status_update = json.loads(data[0].decode('utf-8').split(',', 1)[1])
            update_type = store.Status(status_update["type"])
            update_data = status_update["data"]

            if update_type is store.Status.counts:
                msg = {"response_type": "update_counts", "counts": update_data}
            elif update_type is store.Status.broken_links:
                msg = {"response_type": "update_links", "links": update_data}
            # broken_links = json.loads(data[0].decode('utf-8').split(',', 1)[1])
            # msg = {"response_type": "update",
            #        "broken_links": broken_links}

        elif stream == self.command_stream:
            broken_links = json.loads(data[0].decode('utf-8'))
            msg = {"response_type": "status",
                   "status": "done",
                   "broken_links": broken_links}

        if msg:
            self.write_message(msg)

    def on_close(self):
        print("WebSocket closed")
        # TODO: stop crawling when disconnected

    def check_origin(self, origin):  # TODO: check origin properly
        return True


if __name__ == "__main__":
    options.parse_command_line()
    app = Application()
    app.listen(options.port)
    ioloop.IOLoop.current().start()

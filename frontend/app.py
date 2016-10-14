import zmq
from zmq.eventloop import ioloop, zmqstream
from tornado import websocket, web, ioloop, gen
from tornado.options import define, options
import json
import os.path

import sys
sys.path.append('../broken')
from broken import utils, store

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
            self.index = counter

            ctx = zmq.Context.instance()

            status_socket = ctx.socket(zmq.SUB)
            status_socket.connect('tcp://127.0.0.1:5556')
            status_socket.setsockopt_string(zmq.SUBSCRIBE, str(self.index))

            status_stream = zmqstream.ZMQStream(status_socket)
            status_stream.on_recv(self.handle_reply)

            s = ctx.socket(zmq.PUSH)
            s.connect('tcp://127.0.0.1:5555')
            s.send_pyobj((self.index, url))

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
        print("WebSocket closed")
        # message backend to stop crawling
        if self.index:
            ctx = zmq.Context.instance()
            s = ctx.socket(zmq.PUSH)
            s.connect('tcp://127.0.0.1:5555')
            s.send_pyobj((self.index, None))

    def check_origin(self, origin):  # TODO: check origin properly
        return True


if __name__ == "__main__":
    options.parse_command_line()
    app = Application()
    app.listen(options.port)
    ioloop.IOLoop.current().start()

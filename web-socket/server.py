from tornado import websocket, web, ioloop
import urllib
import json
from broken import main, utils


class MainWebSocketHandler(websocket.WebSocketHandler):
    def open(self):
        print("WebSocket opened")

    def on_message(self, message):
        data = json.loads(message)
        url = data["url"]
        print(url)

        if utils.is_valid_url(url):
            self.write_message({"response_type": "status", "status": "crawling"})
            # main.base_url = url
            # main.main()

    def on_close(self):
        print("WebSocket closed")
        # TODO: stop crawling when disconnected

    def check_origin(self, origin):  # TODO: check origin properly
        return True


def make_app():
    return web.Application([
        (r"/websocket", MainWebSocketHandler),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    ioloop.IOLoop.current().start()

# Stores the number of urls crawled, pages with their associated broken links, etc
import zmq
from zmq.eventloop import ioloop
from tornado import queues
import json
from enum import Enum

ioloop.install()


class Status(Enum):
    counts = 0
    broken_links = 1
    progress = 2


class Store:
    status_socket_created = False

    @classmethod
    def initialize(cls):
        if not cls.status_socket_created:
            ctx = zmq.Context.instance()
            cls.status_socket = ctx.socket(zmq.PUB)
            cls.status_socket.bind('tcp://127.0.0.1:5556')
            cls.status_socket_created = True

    def __init__(self, index):
        Store.initialize()

        self.index = index
        self.base_url = None
        res = {"type": Status.progress.value, "data": "crawling"}
        Store.status_socket.send_string(str(self.index) + "," + json.dumps(res))

        self.queue = queues.Queue()
        self.processing = set()
        self.crawled = set()
        self.broken_links = {}
        self.parent_links = {}

    def add_crawled(self, link):
        self.crawled.add(link)
        res = {"type": Status.counts.value,
               "data": [len(self.crawled), len(self.broken_links)]}
        Store.status_socket.send_string(str(self.index) + "," + json.dumps(res))

    def get_num_broken_links(self):
        return len(self.broken_links)

    def add_broken_link(self, link):
        index = self.get_num_broken_links() + 1
        parent = self.parent_links.get(link, link)
        self.broken_links[link] = {"index": index, "parents": {parent}}
        res = {"type": Status.broken_links.value,
               "data": [{"index": index, "link": link, "parents": [parent]}]}
        Store.status_socket.send_string(str(self.index) + "," + json.dumps(res))

    def add_parent_for_broken_link(self, broken_link, parent_link):
        details = self.broken_links[broken_link]
        details["parents"].add(parent_link)
        res = {"type": Status.broken_links.value,
               "data": [{"index": details["index"], "link": broken_link, "parents": [parent_link]}]}
        Store.status_socket.send_string(str(self.index) + "," + json.dumps(res))

    def get_formatted_broken_links(self):
        res = []
        for broken_link, details in self.broken_links.items():
            index = details["index"]
            parent_pages = details["parents"]
            res.append({"index": index, "link": broken_link, "parents": list(parent_pages)})
        return json.dumps(res)

    def complete(self):
        res = {"type": Status.progress.value, "data": "done"}
        Store.status_socket.send_string(str(self.index) + "," + json.dumps(res))

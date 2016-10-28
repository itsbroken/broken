# Stores the number of urls crawled, pages with their associated broken links, etc

import zmq
import json
from zmq.eventloop import ioloop
from tornado import queues
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

    def __init__(self, index, opts):
        Store.initialize()

        self.index = index
        self.opts = opts
        self.base_url = None
        self.base_url_parsed = None
        self.timed_out = False
        res = {"type": Status.progress.value, "data": "crawling"}
        self.message_ui(json.dumps(res))

        self.queue = queues.Queue()
        self.processing = set()
        self.crawled = set()
        self.broken_links = {}
        self.parent_urls = {}

    def message_ui(self, message, force=False):
        if not self.timed_out or force:
            Store.status_socket.send_string(str(self.index) + "," + message)

    def add_crawled(self, link):
        self.crawled.add(link)
        res = {"type": Status.counts.value,
               "data": [len(self.crawled), len(self.broken_links)]}
        self.message_ui(json.dumps(res))

    def get_num_broken_links(self):
        return len(self.broken_links)

    def add_broken_link(self, link):
        index = self.get_num_broken_links() + 1
        parent = self.parent_urls.get(link.url, link.url)
        self.broken_links[link] = {"index": index, "parents": {parent}}
        res = {"type": Status.broken_links.value,
               "data": [{"index": index, "link": link.url, "type": link.type.value, "parents": [parent]}]}
        self.message_ui(json.dumps(res))

    def add_parent_for_broken_link(self, broken_link, parent_url):
        details = self.broken_links[broken_link]
        details["parents"].add(parent_url)
        res = {"type": Status.broken_links.value,
               "data": [{"index": details["index"], "link": broken_link.url, "type": broken_link.type.value,
                         "parents": [parent_url]}]}
        self.message_ui(json.dumps(res))

    def complete(self):
        res = {"type": Status.progress.value, "data": "done"}
        self.message_ui(json.dumps(res), True)

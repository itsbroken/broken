# Stores the number of urls crawled, pages with their associated broken links, etc

import zmq
import json
from zmq.eventloop import ioloop
from tornado import queues
from enum import Enum

ioloop.install()


class Status(Enum):
    """Various types of status for updating the UI"""
    counts = 0
    broken_links = 1
    progress = 2


class Store:
    """Storage class"""
    status_socket_created = False

    @classmethod
    def initialize(cls):
        # Create a global class socket for the publishing of updates
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

        # Inform subscribers that the crawl has started
        res = {"type": Status.progress.value, "data": "crawling"}
        self.message_subscribers(json.dumps(res))

        self.queue = queues.Queue()
        self.processing = set()
        self.crawled = set()
        self.broken_links = {}
        self.parent_urls = {}

    def message_subscribers(self, message, force=False):
        """Uses the socket class variable to send updates to subscribers"""
        if not self.timed_out or force:
            Store.status_socket.send_string(str(self.index) + "," + message)

    def add_crawled(self, link):
        """Add a link that has been crawled"""
        self.crawled.add(link)
        res = {"type": Status.counts.value,
               "data": [len(self.crawled), len(self.broken_links)]}
        self.message_subscribers(json.dumps(res))

    def get_num_broken_links(self):
        return len(self.broken_links)

    def add_broken_link(self, link):
        """Add a link that has been found to be broken"""
        index = self.get_num_broken_links() + 1
        parent = self.parent_urls.get(link.url, link.url)
        self.broken_links[link] = {"index": index, "parents": {parent}}
        res = {"type": Status.broken_links.value,
               "data": [{"index": index, "link": link.url, "type": link.type.value, "parents": [parent]}]}
        self.message_subscribers(json.dumps(res))

    def add_parent_for_broken_link(self, broken_link, parent_url):
        """Add link where the broken link was found to originate from"""
        details = self.broken_links[broken_link]
        details["parents"].add(parent_url)
        res = {"type": Status.broken_links.value,
               "data": [{"index": details["index"], "link": broken_link.url, "type": broken_link.type.value,
                         "parents": [parent_url]}]}
        self.message_subscribers(json.dumps(res))

    def complete(self):
        """Inform subscribers that the crawl has completed"""
        res = {"type": Status.progress.value, "data": "done"}
        self.message_subscribers(json.dumps(res), True)

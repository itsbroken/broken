# Stores the number of urls crawled, pages with their associated broken links, etc
from tornado import queues


queue = queues.Queue()
processing = set()
crawled = set()
broken_links = {}
parent_links = {}


def get_num_broken_links():
    return len(broken_links)


def add_broken_link(link):
    if link not in broken_links:
        broken_links[link] = set()
    broken_links[link].add(parent_links[link])

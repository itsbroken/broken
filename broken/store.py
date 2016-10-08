# Stores the number of urls crawled, pages with their associated broken links, etc
from tornado import queues


queue = queues.Queue()
processing = set()
crawled = set()
# pages_with_broken_links = {}
pages_with_broken_links = set()

# TODO: Replace this method when we know how to keep track of the parent webpage
def get_num_broken_links():
    return len(pages_with_broken_links)
    # all_broken_links = set()
    # for page, broken_links in pages_with_broken_links.items():
    #     all_broken_links.union(broken_links)
    # return len(all_broken_links)
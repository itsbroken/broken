# Handles the multi-threaded crawling of sites
import time
from datetime import timedelta
from tornado import gen, ioloop

import store
from worker import Worker

num_workers = 10
base_url = "http://www.nus.edu.sg/celc/"


@gen.coroutine
def main():
    start_time = time.time()

    store.queue.put(base_url)

    # Start all workers
    for _ in range(num_workers):
        Worker(base_url)

    # Wait till the queue is empty
    try:
        yield store.queue.join(timeout=timedelta(seconds=20))
    except gen.TimeoutError:  # TEMP: timeout at 20 seconds
        pass

    print("Done in {0:.2f} seconds, crawled {1} URLs, "
          "found {2} broken links".format(time.time() - start_time,
                                          len(store.crawled),
                                          store.get_num_broken_links()))

    for broken_link, parent_link in store.broken_links.items():
        print("{0} linked from: {1}".format(broken_link, parent_link))


if __name__ == '__main__':
    io_loop = ioloop.IOLoop.current()
    io_loop.run_sync(main)

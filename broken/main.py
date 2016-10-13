# Handles the multi-threaded crawling of sites
import zmq

import time
from datetime import timedelta
from tornado import gen, ioloop
import pickle

from store import Store
from worker import Worker

zmq.eventloop.ioloop.install()

num_workers = 10
# Store.requests.put((1, "http://www.nus.edu.sg"))


@gen.coroutine
def main():
    ctx = zmq.Context.instance()
    receiver = ctx.socket(zmq.REP)
    receiver.linger = 0
    receiver.bind('tcp://127.0.0.1:5555')

    while True:
        index, msg = pickle.loads(receiver.recv())
        formatted_broken_links = yield manager(index, msg)
        receiver.send_string(formatted_broken_links)


@gen.coroutine
def manager(index, base_url):
    start_time = time.time()

    store = Store(index)
    store.queue.put(base_url)

    # Start all workers
    workers = [Worker(store) for _ in range(num_workers)]

    # Wait till the queue is empty
    try:
        yield store.queue.join(timeout=timedelta(seconds=20))
    except gen.TimeoutError:  # TEMP: timeout at 20 seconds
        for worker in workers:
            worker.running = False

    print("Done in {0:.2f} seconds, crawled {1} URLs, "
          "found {2} broken links".format(time.time() - start_time,
                                          len(store.crawled),
                                          store.get_num_broken_links()))

    # for broken_link, parent_link in store.broken_links.items():
    #     print("{0} linked from: {1}".format(broken_link, parent_link))

    return store.get_formatted_broken_links()

if __name__ == '__main__':
    io_loop = ioloop.IOLoop.current()
    io_loop.run_sync(main)

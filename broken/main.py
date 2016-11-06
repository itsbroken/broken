import zmq
import time
import pickle
import logging
import sys
from zmq.eventloop import ioloop, zmqstream
from datetime import timedelta
from tornado import gen, ioloop
from store import Store
from worker import Worker
from link import Link

logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

zmq.eventloop.ioloop.install()

num_workers = 10
stores = {}
workers_store = {}


@gen.coroutine
def manager(index, initial_url, opts):
    """
    Main controller of its associated workers and store.
    Creates a store with the initial_url and creates workers to
    crawl links from this URL.

    :param index: Integer index of the manager
    :param initial_url: Initial crawling URL
    :param opts: Options specified by the user
    """
    logging.info("#{} - New crawl request: {} {}".format(index, initial_url, opts))
    start_time = time.time()

    # Initialise a new store
    store = Store(index, opts)
    stores[index] = store
    store.queue.put(Link(initial_url))  # Put the user given link in the queue

    # Start all workers
    workers = [Worker(store) for _ in range(num_workers)]
    workers_store[index] = workers

    # Wait till the queue is empty
    try:
        yield store.queue.join(timeout=timedelta(seconds=opts["crawl_duration"]))
    except gen.TimeoutError:  # Times out after the given crawl duration
        store.timed_out = True
        for worker in workers:
            worker.running = False

    store.complete()  # For telling the store that the crawl is complete

    logging.info("#{0} - Crawled {1} for {2:.2f} seconds, found {3} URLs, "
                 "{4} broken links".format(index, store.base_url,
                                           time.time() - start_time,
                                           len(store.crawled),
                                           store.get_num_broken_links()))


@gen.coroutine
def handle_request(data):
    """
    Handles incoming requests
    :param data: Request data
    """
    index, msg, opts = pickle.loads(data[0])
    if msg is None:  # Signals that a crawl should stop
        for worker in workers_store.get(index, []):  # Get workers of the store
            worker.running = False
        while True:
            try:  # abort queue by calling task_done() many times
                store = stores.get(index)
                if not store:
                    break
                store.queue.task_done()
            except ValueError:
                logging.info('#{} - Crawl aborted'.format(index))
                break
    else:  # Normal request, creates a manager to handle the request
        yield manager(index, msg, opts)


if __name__ == '__main__':
    Store(0, None)  # initialise status socket

    # Listens for incoming messages on the port it's bound to.
    ctx = zmq.Context.instance()
    receiver = ctx.socket(zmq.PULL)
    receiver.bind('tcp://127.0.0.1:5555')
    stream = zmqstream.ZMQStream(receiver)
    stream.on_recv(handle_request)

    ioloop.IOLoop.current().start()

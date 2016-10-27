# Handles the multi-threaded crawling of sites
import zmq
from zmq.eventloop import ioloop, zmqstream
import time
from datetime import timedelta
from tornado import gen, ioloop
import pickle

import logging
import sys
logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

from store import Store
from worker import Worker

zmq.eventloop.ioloop.install()

num_workers = 10
stores = {}
workers_store = {}


@gen.coroutine
def manager(index, initial_url, opts):
    logging.info("#{} - New crawl request: {} {}".format(index, initial_url, opts))
    start_time = time.time()

    store = Store(index, opts)
    stores[index] = store
    store.queue.put(initial_url)

    # Start all workers
    workers = [Worker(store) for _ in range(num_workers)]
    workers_store[index] = workers

    # Wait till the queue is empty
    try:
        yield store.queue.join(timeout=timedelta(seconds=opts["crawl_duration"]))
    except gen.TimeoutError:  # TEMP: timeout at 60 seconds
        store.timed_out = True
        for worker in workers:
            worker.running = False

    store.complete()
    logging.info("#{0} - Crawled {1} for {2:.2f} seconds, found {3} URLs, "
                 "{4} broken links".format(index, store.base_url,
                                           time.time() - start_time,
                                           len(store.crawled),
                                           store.get_num_broken_links()))


@gen.coroutine
def handle_request(data):
    index, msg, opts = pickle.loads(data[0])
    if msg is None:
        for worker in workers_store.get(index, []):
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
    else:
        yield manager(index, msg, opts)

if __name__ == '__main__':
    Store(0, None)  # initialise status socket
    ctx = zmq.Context.instance()
    receiver = ctx.socket(zmq.PULL)
    receiver.bind('tcp://127.0.0.1:5555')
    stream = zmqstream.ZMQStream(receiver)
    stream.on_recv(handle_request)

    ioloop.IOLoop.current().start()

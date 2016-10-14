# Handles the multi-threaded crawling of sites
import zmq
from zmq.eventloop import ioloop, zmqstream
import time
from datetime import timedelta
from tornado import gen, ioloop
import pickle

from store import Store
from worker import Worker

zmq.eventloop.ioloop.install()

num_workers = 10


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

    store.complete()
    print("Crawled {0} for {1:.2f} seconds, found {2} URLs, "
          "{3} broken links".format(base_url,
                                    time.time() - start_time,
                                    len(store.crawled),
                                    store.get_num_broken_links()))


@gen.coroutine
def handle_request(data):
    index, msg = pickle.loads(data[0])
    yield manager(index, msg)

if __name__ == '__main__':
    ctx = zmq.Context.instance()
    receiver = ctx.socket(zmq.PULL)
    receiver.bind('tcp://127.0.0.1:5555')
    stream = zmqstream.ZMQStream(receiver)
    stream.on_recv(handle_request)

    ioloop.IOLoop.current().start()

from tornado import gen, httpclient
from urllib.parse import urlparse
import utils
import html_parser
import other_parsers

import logging
import sys
logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class Worker:
    def __init__(self, store):
        """
        Workers handle the actual sending and receiving of HTTP requests and responses.
        """
        self.store = store
        self.running = True
        self.run()

    @gen.coroutine
    def run(self):
        """
        Called from the constructor. Waits a short moment before processing a url from the queue
        """
        while self.running:
            yield gen.sleep(utils.get_random_delay())
            yield self.process_url()

    @gen.coroutine
    def get_http_response_body_and_effective_url(self, url):

        head_response = yield httpclient.AsyncHTTPClient().fetch(url, method='HEAD')

        if head_response.effective_url not in self.store.crawled:
            if 'Content-Type' in head_response.headers and \
                    not utils.is_supported_content_type(head_response.headers['Content-Type']):
                return None, None
            else:
                response = yield httpclient.AsyncHTTPClient().fetch(url, method='GET')
                return response.body, response.effective_url
        else:
            return None, None

    @gen.coroutine
    def get_http_header_response(self, url):
        head_response = yield httpclient.AsyncHTTPClient().fetch(url, method='HEAD')

        if head_response.effective_url not in self.store.crawled:
            return head_response
        return None

    @gen.coroutine
    def get_http_full_response(self, url):
        response = yield httpclient.AsyncHTTPClient().fetch(url, method='GET')

        if response.effective_url not in self.store.crawled:
            return response
        return None

    def queue_additional_links(self, url, response):
        """
        Parses through a HTML response for HTTP links

        :param url: Base / Parent URL
        :param response: The Tornado HTTP Response Object from a fetch of the url
        :return:
        """

        if 'Content-Type' in response.headers and \
                utils.is_supported_content_type(response.headers['Content-Type']):

            effective_url = response.effective_url
            response_body = response.body

            # Extract links
            found_links = html_parser.extract_links(effective_url, response_body)
            for link in found_links:
                link_host = urlparse(link).netloc.lower()
                if link_host == self.store.base_host:  # Only allow links that stem from the base host
                    self.store.parent_links[link] = url  # Keep track of the parent of the found link
                    if link in self.store.broken_links:  # Add links that lead to this broken link
                        self.store.add_parent_for_broken_link(link, url)
                    yield self.store.queue.put(link)

    @gen.coroutine
    def process_url(self):
        """
        Gets a URL from the queue and checks if it needs to be handled by special rules or crawled as per normal
        """
        url = yield self.store.queue.get()
        if not urlparse(url).scheme:
            url = 'http://' + url
        try:
            if url in self.store.processing \
                    or url in self.store.crawled:
                return

            # print("Processing {}".format(url))
            self.store.processing.add(url)

            try:
                response = yield self.get_http_full_response(url)
                # print("Received {}".format(url))
                if not response:
                    return

                effective_url = response.effective_url

                if not self.store.base_url:
                    self.store.base_url = effective_url
                    self.store.base_host = urlparse(effective_url).netloc.lower()

                # Check for links to Content Hosting Sites that do not fully follow HTTP Error Codes internally
                if not other_parsers.is_special_link(response):
                    yield from self.queue_additional_links(url, response)

            except httpclient.HTTPError as e:
                if e.code in range(400, 500):
                    logging.info("{}, {}".format(e.code, url))
                    self.store.add_broken_link(url)
                else:
                    logging.info("{} {}".format(e, url))
            except Exception as e:
                logging.warning("Exception: {}, {}".format(e, url), exc_info=1)
            finally:
                if url != self.store.base_url and url in self.store.parent_links:
                    del self.store.parent_links[url]  # Remove entry in parent link to save space
                self.store.processing.remove(url)
                self.store.add_crawled(url)

        finally:
            try:
                self.store.queue.task_done()
            except ValueError:  # queue was aborted
                pass


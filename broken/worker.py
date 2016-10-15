from tornado import gen, httpclient
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

    def process_regular_url(self, effective_url, response_body, url):
        """
        Parses through the response for HTTP links

        :param effective_url: URL after redirects are handled
        :param response_body: The HTTP Response obtained from exploring the effective_url
        :param url: Parent URL
        :return:
        """
        # Extract links
        found_links = html_parser.extract_links(effective_url, response_body)
        for link in found_links:
            if link.startswith(self.store.base_url):  # Only allow links that stem from the base url
                self.store.parent_links[link] = url  # Keep track of the parent of the found link
                if link in self.store.broken_links:  # Add links that lead to this broken link
                    self.store.add_parent_for_broken_link(link, url)
                yield self.store.queue.put(link)

    def process_imageshack_url(self, effective_url, response_body, url):
        """
        Checks to see if content hosted on Imageshack is still valid

        :param effective_url: URL after redirects are handled
        :param response_body: The HTTP Response obtained from exploring the effective_url
        :param url: Parent URL
        :return:
        """
        if other_parsers.is_removed_imageshack_content(response_body):
            self.store.add_broken_link(effective_url)
            self.store.add_parent_for_broken_link(effective_url, url)

    @gen.coroutine
    def process_url(self):
        """
        Gets a URL from the queue and checks if it needs to be handled by special rules or crawled as per normal
        """
        url = yield self.store.queue.get()
        try:
            if url in self.store.processing \
                    or url in self.store.crawled:
                return

            # print("Processing {}".format(url))
            self.store.processing.add(url)

            try:
                response_body, effective_url = yield self.get_http_response_body_and_effective_url(url)
                # print("Received {}".format(url))

                if not self.store.base_url:
                    self.store.base_url = effective_url

                # Check for links to Content Hosting Sites that do not follow HTTP Error Codes internally
                if "imageshack" in effective_url:
                    yield from self.process_imageshack_url(effective_url, response_body, url)
                elif False:
                    pass
                else:
                    yield from self.process_regular_url(effective_url, response_body, url)

            except httpclient.HTTPError as e:
                if e.code in range(400, 500):
                    logging.info("{}, {}".format(e.code, url))
                    self.store.add_broken_link(url)
                else:
                    logging.info(e, url)
            except Exception as e:
                logging.warning("Exception: {}, {}".format(e, url))

            if url != self.store.base_url and url in self.store.parent_links:
                del self.store.parent_links[url]  # Remove entry in parent link to save space
            self.store.processing.remove(url)
            self.store.add_crawled(url)

        finally:
            try:
                self.store.queue.task_done()
            except ValueError:  # queue was aborted
                pass


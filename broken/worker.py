import utils
import html_parser
import other_parsers
import logging
import sys
from tornado import gen, httpclient
from urllib.parse import urlparse
from link import LinkType

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
    def get_http_full_response(self, url):
        response = yield httpclient.AsyncHTTPClient().fetch(url, method='GET')

        if response.effective_url not in self.store.crawled:
            return response
        return None

    def queue_additional_links(self, parent_url, response):
        """
        Parses through a HTML response for HTTP links

        :param parent_url: Parent URL
        :param response: The Tornado HTTP Response Object from a fetch of parent_url
        :return:
        """

        if not utils.is_supported_content_type(response.headers.get('Content-Type')):
            return
        check_images = self.store.opts["check_images"]
        check_videos = self.store.opts["check_videos"]
        # Extract links
        found_links = html_parser.extract_links(response.effective_url, response.body, check_images, check_videos)

        for link in found_links:
            if link.type is LinkType.regular:
                link_parsed = urlparse(link.url)
                base_parsed = self.store.base_url_parsed

                if self.store.opts["limit_to_url"]:
                    is_link_allowed = (link_parsed.netloc.lower() == base_parsed.netloc.lower() and
                                       link_parsed.path == base_parsed.path and
                                       link_parsed.params == base_parsed.params and
                                       link_parsed.query == base_parsed.query)
                else:
                    is_link_allowed = link_parsed.netloc.lower() == base_parsed.netloc.lower()

                if not is_link_allowed:
                    continue

            self.store.parent_urls[link.url] = parent_url  # Keep track of the parent of the found link
            if link.url in self.store.broken_links:  # Add links that lead to this broken link
                self.store.add_parent_for_broken_link(link, parent_url)
            else:
                yield self.store.queue.put(link)

    @gen.coroutine
    def process_url(self):
        """
        Gets a URL from the queue and checks if it needs to be handled by special rules or crawled as per normal
        """
        link = yield self.store.queue.get()
        if not urlparse(link.url).scheme:
            link.url = 'http://' + link.url

        try:
            if link in self.store.processing or link in self.store.crawled:
                return

            # print("Processing {}".format(url))
            self.store.processing.add(link)

            try:
                response = yield self.get_http_full_response(link.url)
                # print("Received {}".format(url))
                if not response:
                    return

                effective_url = response.effective_url

                if not self.store.base_url:
                    self.store.base_url = effective_url
                    self.store.base_url_parsed = urlparse(effective_url)

                if link.type is LinkType.regular:
                    yield from self.queue_additional_links(link.url, response)

                elif link.type is LinkType.image:
                    other_parsers.assert_valid_image_link(response)

                elif link.type is LinkType.video:
                    other_parsers.assert_valid_video_link(response)

            except httpclient.HTTPError as e:
                if e.code in range(400, 500):
                    logging.info("#{} - {}, {}".format(self.store.index, e.code, link.url))
                    self.store.add_broken_link(link)
                else:
                    logging.info("#{} - {} {}".format(self.store.index, e, link.url))

            except Exception as e:
                logging.warning("#{} - Exception: {}, {}".format(self.store.index, e, link.url), exc_info=1)

            finally:
                if link.url != self.store.base_url and link.url in self.store.parent_urls:
                    del self.store.parent_urls[link.url]  # Remove entry in parent link to save space
                self.store.processing.remove(link)
                self.store.add_crawled(link)

        finally:
            try:
                self.store.queue.task_done()
            except ValueError:  # queue was aborted
                pass


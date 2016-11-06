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

UA_STRING = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.87 Safari/537.36"


class Worker:
    def __init__(self, store):
        """Workers handle the actual sending and receiving of HTTP requests and responses."""
        self.store = store
        self.running = True
        self.run()

    @gen.coroutine
    def run(self):
        """Called from the constructor. Waits a short moment before processing a url from the queue"""
        while self.running:
            yield gen.sleep(utils.get_random_delay())
            yield self.process_url()

    @gen.coroutine
    def get_http_full_response(self, url):
        response = yield httpclient.AsyncHTTPClient().fetch(url, method='GET', user_agent=UA_STRING)

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

        if not utils.is_text_content_type(response.headers.get('Content-Type')):
            return
        check_images = self.store.opts["check_images"]
        check_videos = self.store.opts["check_videos"]

        # Extract links
        found_links = html_parser.extract_links(response.effective_url, response.body, check_images, check_videos)

        for link in found_links:
            self.store.parent_urls[link.url] = parent_url  # Keep track of the parent of the found link
            if link in self.store.broken_links:  # Add links that lead to this broken link
                self.store.add_parent_for_broken_link(link, parent_url)
            else:
                yield self.store.queue.put(link)

    @gen.coroutine
    def process_url(self):
        """
        Gets a URL from the queue and checks if it needs to be handled by special rules or crawled as per normal
        """
        link = yield self.store.queue.get()
        link_parsed = urlparse(link.url)
        if not link_parsed.scheme:
            link.url = 'http://' + link.url

        try:
            if link in self.store.processing or link in self.store.crawled:
                return

            # print("Processing {}".format(link.url))
            self.store.processing.add(link)

            try:
                response = yield self.get_http_full_response(link.url)
                if not response:
                    return

                is_initial_link = not self.store.base_url

                if is_initial_link:
                    effective_url = response.effective_url
                    self.store.base_url = effective_url
                    self.store.base_url_parsed = urlparse(effective_url)

                if link.type is LinkType.regular:
                    base_parsed = self.store.base_url_parsed
                    limit_to_url = self.store.opts["limit_to_url"]
                    if utils.is_link_allowed(link_parsed, base_parsed, limit_to_url) or is_initial_link:
                        yield from self.queue_additional_links(link.url, response)

                elif link.type is LinkType.image:
                    other_parsers.assert_valid_image_link(link.url, response)

                elif link.type is LinkType.video:
                    other_parsers.assert_valid_video_link(link.url, response)

            except httpclient.HTTPError as e:
                if e.code in range(400, 500) and e.code not in [401]:
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

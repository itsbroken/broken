from tornado import gen, httpclient
import utils
import html_parser


class Worker:
    def __init__(self, store, base_url):
        """
        Workers handle the actual sending and receiving of HTTP requests and responses.

        :param base_url: base URL of the entire app, crawling takes place within the subtree rooted at this url
        """
        self.store = store
        self.base_url = base_url
        self.running = True
        self.run()

    @gen.coroutine
    def run(self):
        """
        Called from the constructor. Waits a sort moment before processing a url from the queue
        """
        while self.running:
            yield gen.sleep(utils.get_random_delay())
            yield self.process_url()

    @gen.coroutine
    def process_url(self):
        """
        Gets a url from the queue and checks if it needs to be handled by special rules or crawled as per normal
        """
        url = yield self.store.queue.get()
        try:
            if url in self.store.processing \
                    or url in self.store.crawled:
                return

            # print("Processing {}".format(url))
            self.store.processing.add(url)

            # Check special rules for this url
            # If special url, let the specials module handle
            # Else, continue to get the HTTP response

            # Get response from URL
            try:
                response_body, effective_url = yield self.get_http_response_body_and_effective_url(url)
                # print("Received {}".format(url))

                # Extract links
                found_links = html_parser.extract_links(effective_url, response_body)

                for link in found_links:
                    if link.startswith(self.base_url):  # Only allow links that stem from the base url
                        self.store.parent_links[link] = url  # Keep track of the parent of the found link
                        if link in self.store.broken_links:  # Add links that lead to this broken link
                            self.store.add_parent_for_broken_link(link, url)
                        yield self.store.queue.put(link)

            except httpclient.HTTPError as e:
                if e.code == 404:
                    print("404,", url)
                    self.store.add_broken_link(url)
                else:
                    print(e, url)
            except Exception as e:
                print("Exception: {0}, {1}".format(e, url))

            finally:
                if url != self.base_url and url in self.store.parent_links:
                    del self.store.parent_links[url]  # Remove entry in parent link to save space
                self.store.processing.remove(url)
                self.store.add_crawled(url)

        finally:
            self.store.queue.task_done()

    @gen.coroutine
    def get_http_response_body_and_effective_url(self, url):
        head_response = yield httpclient.AsyncHTTPClient().fetch(url, method='HEAD')

        if utils.is_supported_content_type(head_response.headers["Content-Type"]) \
                and head_response.effective_url not in self.store.crawled:
            response = yield httpclient.AsyncHTTPClient().fetch(url, method='GET')
            return response.body, response.effective_url
        else:
            return None, None

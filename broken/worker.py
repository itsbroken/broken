from tornado import gen, httpclient
import store
import utils
import html_parser


class Worker:
    def __init__(self, base_url):
        """
        Workers handle the actual sending and receiving of HTTP requests and responses.

        :param base_url: base URL of the entire app, crawling takes place within the subtree rooted at this url
        """
        self.base_url = base_url
        self.run()

    @gen.coroutine
    def run(self):
        """
        Called from the constructor. Waits a sort moment before processing a url from the queue
        """
        while True:
            yield gen.sleep(utils.get_random_delay())
            yield self.process_url()

    @gen.coroutine
    def process_url(self):
        """
        Gets a url from the queue and checks if it needs to be handled by special rules or crawled as per normal
        """
        url = yield store.queue.get()
        try:
            if url in store.processing \
               or url in store.crawled:
                return

            print("Processing {}".format(url))
            store.processing.add(url)

            # Check special rules for this url
            # If special url, let the specials module handle
            # Else, continue to get the HTTP response

            # Get response from URL
            try:
                print("Received {}".format(url))
                response_body = yield self.get_http_response_body(url)

                # Extract links
                found_links = html_parser.extract_links(url, response_body)

                for link in found_links:
                    if link.startswith(self.base_url):  # Only allow links that stem from the base url
                        store.parent_links[link] = url  # Keep track of the parent of the found link
                        if link in store.broken_links:  # Add links that lead to this broken link
                            store.broken_links[link].add(url)
                        yield store.queue.put(link)

            except httpclient.HTTPError as e:
                if e.code == 404:
                    print("404,", url)
                    store.add_broken_link(url)

            except Exception as e:
                print("Exception: {0}, {1}".format(e, url))

            finally:
                if url != self.base_url:
                    del store.parent_links[url]  # Remove entry in parent link to save space
                store.processing.remove(url)
                store.crawled.add(url)

        finally:
            store.queue.task_done()

    @gen.coroutine
    def get_http_response_body(self, url):
        head_response = yield httpclient.AsyncHTTPClient().fetch(url, method='HEAD')

        if utils.is_supported_content_type(head_response.headers["Content-Type"]):
            response = yield httpclient.AsyncHTTPClient().fetch(url, method='GET')
            return response.body
        else:
            return None

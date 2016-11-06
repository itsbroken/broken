# Various Parsers for html returned by various Content-Hosting-Sites

import utils
from tornado import httpclient
from bs4 import BeautifulSoup
from urllib.parse import urlparse


def is_imageshack_link(url):
    return urlparse(url).netloc.lower() == 'imageshack.com'


def is_removed_imageshack_content(response_body):
    """
    Decides if a received response obtained from crawling an Imageshack link contains valid content or not.
    Accurate as on 15/10/2016.

    :param response_body:
    :return: Whether the given response is a landing page for removed or unavailable content
    """

    html_tree = BeautifulSoup(response_body, 'html.parser')

    if html_tree.find('section', class_='four-oh-four') is not None:
        return True
    elif html_tree.find('div', id='unavailable-lp') is not None:
        return True

    return False


def assert_valid_imageshack_link(response):
    """
    Asserts the accessibility of content hosted at ImageShack links

    :param response: The Tornado HTTP Response Object from a fetch of the Link
    :return:
    """

    response_body = response.body

    if is_removed_imageshack_content(response_body):
        raise httpclient.HTTPError(code=404)


def is_tinypic_link(url):
    return urlparse(url).netloc.lower() == 'tinypic.com'


def assert_valid_tinypic_link(response):
    """
    Asserts the accessibility of content hosted at TinyPic links

    :param response: The Tornado HTTP Response Object from a fetch of the Link
    :return:
    """

    if urlparse(response.effective_url).path == '/images/404.gif':
        raise httpclient.HTTPError(code=404)


def assert_valid_generic_image_link(response):
    if not utils.is_image_content_type(response.headers.get('Content-Type')):
        raise httpclient.HTTPError(code=404)


def assert_valid_image_link(response):
    url = response.effective_url

    if is_imageshack_link(url):
        assert_valid_imageshack_link(response)

    elif is_tinypic_link(url):
        assert_valid_tinypic_link(response)

    else:
        assert_valid_generic_image_link(response)


def assert_valid_generic_video_link(response):
    if not utils.is_video_content_type(response.headers.get('Content-Type')):
        raise httpclient.HTTPError(code=404)


def assert_valid_video_link(response):

    url = response.effective_url

    if is_youtube_link(url):
        assert_valid_youtube_link(response)
    """
    else:
        assert_valid_generic_video_link(response)
    """


def is_youtube_link(url):
    return urlparse(url).netloc.lower() == 'www.youtube.com'


def is_removed_youtube_content(response_body):
    """
    Decides if a received response obtained from crawling an Youtube link contains valid content or not.
    Accurate as on 11/4/2016.

    :param response_body:
    :return: Whether the given response is a landing page for removed or unavailable content
    """

    html_tree = BeautifulSoup(response_body, 'html.parser')

    for tag in html_tree.find_all(id='unavailable-message'):
        if 'This video is no longer available due to a copyright claim by' in str(tag.string):
            return True

    return False


def assert_valid_youtube_link(response):
    """
    Asserts the accessibility of content hosted at YouTube links

    :param response: The Tornado HTTP Response Object from a fetch of the Link
    :return:
    """

    response_body = response.body

    if is_removed_youtube_content(response_body):
        raise httpclient.HTTPError(code=404)


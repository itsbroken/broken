# Various Parsers for html returned by various Content-Hosting-Sites

import utils
import io
import hashlib
from tornado import httpclient
from bs4 import BeautifulSoup
from urllib.parse import urlparse


def is_imgur_link(url):
    return 'imgur' in urlparse(url).netloc.lower()


def assert_valid_imgur_link(response):
    """
    Asserts the accessibility of content hosted at Imgur links. Accurate as of 6/11/2016.

    :param response: The Tornado HTTP Response Object from a fetch of the Link
    :return:
    """

    response_body = response.body

    if urlparse(response.effective_url).path == '/removed.png':
        raise httpclient.HTTPError(code=404)


def is_imageshack_link(url):
    return 'imageshack' in urlparse(url).netloc.lower()


def assert_valid_imageshack_link(response):
    """
    Asserts the accessibility of content hosted at ImageShack links. Accurate as of 6/11/2016.

    :param response: The Tornado HTTP Response Object from a fetch of the Link
    :return:
    """

    response_body = response.body

    html_tree = BeautifulSoup(response_body, 'html.parser')

    if html_tree.find('section', class_='four-oh-four') is not None:
        raise httpclient.HTTPError(code=404)
    elif html_tree.find('div', id='unavailable-lp') is not None:
        raise httpclient.HTTPError(code=404)


def is_photobucket_link(url):
    return 'photobucket' in urlparse(url).netloc.lower()


def assert_valid_photobucket_link(response):
    """
    Asserts the accessibility of content hosted at Photobucket links. Accurate as of 6/11/2016.

    :param response: The Tornado HTTP Response Object from a fetch of the Link
    :return:
    """

    response_body = response.body

    image_data = io.BytesIO(response_body).getvalue()

    hasher = hashlib.md5()

    hasher.update(image_data)

    if hasher.hexdigest() == 'b663c32ab7ecad43166c7087f12a51c9':
        raise httpclient.HTTPError(code=404)


def is_tinypic_link(url):
    return 'tinypic' in urlparse(url).netloc.lower()


def assert_valid_tinypic_link(response):
    """
    Asserts the accessibility of content hosted at TinyPic links. Accurate as of 6/11/2016.

    :param response: The Tornado HTTP Response Object from a fetch of the Link
    :return:
    """

    if urlparse(response.effective_url).path == '/images/404.gif':
        raise httpclient.HTTPError(code=404)


def is_flickr_link(url):
    return 'flickr' in urlparse(url).netloc.lower()


def assert_valid_flickr_link(response):
    """
    Asserts the accessibility of content hosted at Flickr links. Accurate as of 6/11/2016.

    :param response: The Tornado HTTP Response Object from a fetch of the Link
    :return:
    """

    if 'photo_unavailable' in urlparse(response.effective_url).path:
        raise httpclient.HTTPError(code=404)


def assert_valid_generic_image_link(response):
    """
    Asserts that the response is of type image/*.

    :param response: The Tornado HTTP Response Object from a fetch of the Link
    :return:
    """

    if not utils.is_image_content_type(response.headers.get('Content-Type')):
        raise httpclient.HTTPError(code=404)


def assert_valid_image_link(base_url, response):
    """
    Determines if the supplied url involves an external image hosting site, and checks if the content is still valid.

    :param base_url: The raw URL supplied with an image-related tag.
    :param response: The Tornado HTTP Response Object from a fetch of the Link
    :return:
    """

    if is_imgur_link(base_url):
        assert_valid_imgur_link(response)

    elif is_imageshack_link(base_url):
        assert_valid_imageshack_link(response)

    elif is_photobucket_link(base_url):
        assert_valid_photobucket_link(response)

    elif is_tinypic_link(base_url):
        assert_valid_tinypic_link(response)

    elif is_flickr_link(base_url):
        assert_valid_flickr_link(response)

    else:
        assert_valid_generic_image_link(response)


def is_youtube_link(url):
    return 'youtube' in urlparse(url).netloc.lower()


def assert_valid_youtube_link(response):
    """
    Asserts the accessibility of content hosted at YouTube links. Accurate as of 6/11/2016.

    :param response: The Tornado HTTP Response Object from a fetch of the Link
    :return:
    """

    response_body = response.body

    html_tree = BeautifulSoup(response_body, 'html.parser')

    for tag in html_tree.find_all(id='unavailable-message'):
        if 'This video is no longer available due to a copyright claim by' in str(tag.string):
            raise httpclient.HTTPError(code=404)


def assert_valid_generic_video_link(response):
    if not utils.is_video_content_type(response.headers.get('Content-Type')):
        raise httpclient.HTTPError(code=404)


def assert_valid_video_link(base_url, response):

    if is_youtube_link(base_url):
        assert_valid_youtube_link(response)



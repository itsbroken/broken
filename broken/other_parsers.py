# Various Parsers for html returned by various Content-Hosting-Sites

import utils
import io
import hashlib
from tornado import httpclient
from bs4 import BeautifulSoup
from urllib.parse import urlparse


def is_imgur_link(url):
    return utils.is_domain_or_subdomain(url, 'imgur.com')


def assert_valid_imgur_link(response):
    """
    Asserts the accessibility of content hosted at Imgur links. Accurate as of 6/11/2016.

    :param response: The Tornado HTTP Response Object from a fetch of the Link
    :return:
    """

    if urlparse(response.effective_url).path == '/removed.png':
        raise httpclient.HTTPError(code=404)


def is_photobucket_link(url):
    return utils.is_domain_or_subdomain(url, 'photobucket.com')


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
    return utils.is_domain_or_subdomain(url, 'tinypic.com')


def assert_valid_tinypic_link(response):
    """
    Asserts the accessibility of content hosted at TinyPic links. Accurate as of 6/11/2016.

    :param response: The Tornado HTTP Response Object from a fetch of the Link
    :return:
    """

    if urlparse(response.effective_url).path == '/images/404.gif':
        raise httpclient.HTTPError(code=404)


def is_yimg_link(url):
    return utils.is_domain_or_subdomain(url, 'yimg.com')


def assert_valid_yimg_link(response):
    """
    Asserts the accessibility of content hosted at Yimg links. Accurate as of 6/11/2016.

    :param response: The Tornado HTTP Response Object from a fetch of the Link
    :return:
    """

    if urlparse(response.effective_url).path.startswith('/pw/images/en-us/photo_unavailable_'):
        raise httpclient.HTTPError(code=404)


def assert_valid_generic_image_link(response):
    """
    Asserts that the response is of type image/*.

    :param response: The Tornado HTTP Response Object from a fetch of the Link
    :return:
    """

    if not utils.is_image_content_type(response.headers.get('Content-Type')):
        raise httpclient.HTTPError(code=404)


def assert_valid_image_link(response):
    """
    Determines if the supplied url involves an external image hosting site, and checks if the content is still valid.

    Note:
    1) Invalid Imageshack Links will be caught by the generic image checker.
    2) Invalid Flickr Links will redirect to a invalid photo file on Yahoo Images.

    :param response: The Tornado HTTP Response Object from a fetch of the Link
    :return:
    """
    base_url = response.effective_url

    if is_imgur_link(base_url):
        assert_valid_imgur_link(response)

    elif is_photobucket_link(base_url):
        assert_valid_photobucket_link(response)

    elif is_tinypic_link(base_url):
        assert_valid_tinypic_link(response)

    elif is_yimg_link(base_url):
        assert_valid_yimg_link(response)

    assert_valid_generic_image_link(response)


def is_youtube_link(url):
    return utils.is_domain_or_subdomain(url, 'youtube.com')


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


def assert_valid_video_link(response):
    """
    Determines if the supplied url involves an external video hosting site, and checks if the content is still valid.

    :param response: The Tornado HTTP Response Object from a fetch of the Link
    :return:
    """

    base_url = response.effective_url

    if is_youtube_link(base_url):
        assert_valid_youtube_link(response)



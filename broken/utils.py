import random
import re
from urllib.parse import urlparse


def get_random_delay(min_time=0.01, max_time=0.1):
    """
    Random sleep time between min and max time. Defaults to between 10 and 100ms

    :param min_time: minimum time (s)
    :param max_time: maximum time (s)
    :return: time in seconds
    """
    return random.uniform(min_time, max_time)


def is_text_content_type(raw_content_type):
    """
    Checks if the raw content type retrieved from the header is of
    the appropriate type for more links to be found from the given URL

    :param raw_content_type: raw content type header data
    :return:
    """
    return not raw_content_type or re.match(r'text/', raw_content_type)


def is_image_content_type(raw_content_type):
    """
    Checks if the raw content type retrieved from the header is of
    the appropriate type for Images

    :param raw_content_type: raw content type header data
    :return:
    """

    return not raw_content_type or re.match(r'image/', raw_content_type)


def is_video_content_type(raw_content_type):
    """
    Checks if the raw content type retrieved from the header is of
    the appropriate type for Videos

    :param raw_content_type: raw content type header data
    :return:
    """

    return not raw_content_type or re.match(r'video/', raw_content_type)


def is_valid_url(url):
    if not re.match(r'https?://', url):
        url = "http://" + url
    parsed = urlparse(url)
    return parsed.netloc


def is_link_allowed(link_parsed, base_parsed, limit_to_url):
    if limit_to_url:
        return (link_parsed.netloc.lower() == base_parsed.netloc.lower() and
                link_parsed.path == base_parsed.path and
                link_parsed.params == base_parsed.params and
                link_parsed.query == base_parsed.query)
    else:
        return link_parsed.netloc.lower() == base_parsed.netloc.lower()

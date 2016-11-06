# Parses html to extract and return links, images and videos

import re
from bs4 import BeautifulSoup, SoupStrainer
from urllib.parse import urlparse, urljoin, urldefrag, quote
from link import Link, LinkType


def extract_links(url, response_body, include_images, include_videos):
    """
    Extract all links from the response body

    :param url: URL of the response
    :param response_body: body of the HTTP response
    :param include_images: whether to include image links
    :param include_videos: whether to include video links
    :return: set of Links that were found
    """
    if response_body is None:
        return []

    response_body = BeautifulSoup(response_body, "html.parser").prettify()

    found_links = set()
    extract_href_links(found_links, url, response_body)
    if include_images:
        extract_img_src_links(found_links, url, response_body)
    if include_videos:
        extract_video_src_links(found_links, url, response_body)

    return found_links


def extract_href_links(found_links, url, response_body):
    """
    Find href links in the given response_body and adds them to the
    given found_links list.

    :param found_links: List where the found links will be added to
    :param url: URL where the response was retrieved
    :param response_body: Response from the URL
    """
    base_href = url

    for base_link in BeautifulSoup(response_body,
                                   "html.parser",
                                   parse_only=SoupStrainer('base', href=True)):
        base_href = base_link["href"].strip()
        if not urlparse(base_href).scheme:
            base_href = normalize_url(url, base_href)
        break

    for found_link in BeautifulSoup(response_body,
                                    "html.parser",
                                    parse_only=SoupStrainer('a', href=True)):
        a_href = found_link["href"].strip()
        if re.match(r'javascript:|mailto:|tel:', a_href):
            continue
        found_links.add(Link(normalize_url(base_href, a_href), LinkType.regular))


def extract_img_src_links(found_links, url, response_body):
    """
    Find image source links.

    :param found_links: List where the found image links will be added to
    :param url: URL where the response was retrieved
    :param response_body: Response from the URL
    """
    for found_img in BeautifulSoup(response_body,
                                   "html.parser",
                                   parse_only=SoupStrainer(['img', 'embed'], src=True)):
        img_src = found_img["src"].strip()
        found_links.add(Link(normalize_url(url, img_src), LinkType.image))


def extract_video_src_links(found_links, url, response_body):
    """
    Find video source links

    :param found_links: List where the found video links will be added to
    :param url: URL where the response was retrieved
    :param response_body: Response from the URL
    """
    for found_embed in BeautifulSoup(response_body,
                                     "html.parser",
                                     parse_only=SoupStrainer(['video', 'embed', 'iframe'], src=True)):
        vid_src = found_embed["src"].strip()
        found_links.add(Link(normalize_url(url, vid_src), LinkType.video))


def normalize_url(parent_link, found_link):
    """
    Removes unnecessary parts in a url (e.g fragments)
    Converts relative links to absolute links based on the given url

    :param parent_link: URL where found_link was found
    :param found_link: link obtained from a href tag
    :return: normalized link
    """
    link_without_fragment = urldefrag(found_link)[0]  # Fragments refer to hash links
    absolute_link = urljoin(parent_link, link_without_fragment.strip())
    return quote(absolute_link, safe="%/:=&?~#+!$,;'@()*[]")  # http://bugs.python.org/issue918368

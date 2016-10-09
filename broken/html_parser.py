# Parses html to extract and return links, images and videos

from bs4 import BeautifulSoup, SoupStrainer
from urllib.parse import urljoin, urldefrag, quote
import re


def extract_links(url, response_body):
    """
    Extract all links from the response body

    :param url: URL of the response
    :param response_body: body of the HTTP response
    :return: list of links that were found
    """
    if response_body is None:
        return []

    found_links = []
    extract_href_links(found_links, url, response_body)
    extract_img_src_links(found_links, url, response_body)

    return found_links


def extract_href_links(found_links, url, response_body):
    for found_link in BeautifulSoup(response_body, "html.parser", parse_only=SoupStrainer('a', href=True)):
        link = found_link["href"].strip()
        if re.match(r'javascript:|mailto:', link):
            continue
        found_links.append(normalize_url(url, link))


def extract_img_src_links(found_links, url, response_body):
    for found_img in BeautifulSoup(response_body, "html.parser", parse_only=SoupStrainer('img', src=True)):
        img_src = found_img["src"].strip()
        found_links.append(normalize_url(url, img_src))


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

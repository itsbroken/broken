from broken.html_parser import *


def test_extract_links():
    html = """
    <html>
    <a href="http://www.google.com">Google</a>
    <a href="http://nus.edu.sg">NUS</a>
    </html>
    """
    links = ["http://www.google.com", "http://nus.edu.sg"]
    assert extract_links(None, html) == links


def test_extract_links_with_space():
    html = """
    <html>
    <a href="http://www.google.com         ">Google</a>
    <a href="http://nus.edu.sg ">NUS</a>
    </html>
    """
    links = ["http://www.google.com", "http://nus.edu.sg"]
    assert extract_links(None, html) == links


# TODO: Handle this error
def test_extract_links_with_javascript():
    html = """
    <a href="javascript:void(0)"></a>
    """
    links = []
    assert extract_links(None, html) == links


# TODO: Handle this error
def test_normalize_link_similar_base_url():
    base_url = "http://www.google.com"
    found_link = "google.com"
    assert normalize_link(base_url, found_link) == base_url


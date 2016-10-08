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


def test_extract_links_with_javascript():
    html = """
    <a href="  javascript:void(0)"></a>
    <a href="javascript:void(0)"></a>
    """
    links = []
    assert extract_links(None, html) == links


def test_extract_links_with_mailto():
    html = """
    <a href="  mailto:sebastian@u.nus.edu"></a>
    <a href="mailto:sebastian@u.nus.edu"></a>
    """
    links = []
    assert extract_links(None, html) == links
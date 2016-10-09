from broken.html_parser import *


def test_extract_href_links():
    html = """
    <html>
    <a href="http://www.google.com">Google</a>
    <a href="http://nus.edu.sg">NUS</a>
    </html>
    """
    links = {"http://www.google.com", "http://nus.edu.sg"}
    found_links = set()
    extract_href_links(found_links, None, html)
    assert found_links == links


def test_extract_href_links_with_space():
    html = """
    <html>
    <a href="http://www.google.com         ">Google</a>
    <a href="http://nus.edu.sg ">NUS</a>
    </html>
    """
    links = {"http://www.google.com", "http://nus.edu.sg"}
    found_links = set()
    extract_href_links(found_links, None, html)
    assert found_links == links


def test_extract_href_links_with_javascript():
    html = """
    <a href="  javascript:void(0)"></a>
    <a href="javascript:void(0)"></a>
    """
    found_links = set()
    extract_href_links(found_links, None, html)
    assert len(found_links) == 0


def test_extract_href_links_with_mailto():
    html = """
    <a href="  mailto:sebastian@u.nus.edu"></a>
    <a href="mailto:sebastian@u.nus.edu"></a>
    """
    found_links = set()
    extract_href_links(found_links, None, html)
    assert len(found_links) == 0


def test_extract_img_src_links():
    html = """
    <img src="image.png">
    <img src="image.png" />
    <img src="image.png"></img>
    """
    img_links = {"http://website.com/image.png"}
    found_links = set()
    extract_img_src_links(found_links, "http://website.com", html)
    assert found_links == img_links

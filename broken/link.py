from enum import Enum


class LinkType(Enum):
    regular = "url"
    image = "image"
    video = "video"


class Link:
    """Represents the various types of links"""
    def __init__(self, url, link_type=LinkType.regular):
        self.type = link_type
        self.url = url

    def __str__(self):
        return "<{} ({} link)>".format(self.url, self.type)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.type == other.type and self.url == other.url

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.url)

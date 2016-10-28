from enum import Enum


class Type(Enum):
    regular = 0
    image = 1
    video = 2


class Link:
    def __init__(self, url, link_type=0):
        self.type = link_type
        self.url = url

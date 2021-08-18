#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

# This file is only used if you use `make publish` or
# explicitly specify it as your config file.

import os
import sys

sys.path.append(os.curdir)
from pelicanconf import *


SITEURL = "https://lee-w.github.io/travlog"
SITELOGO = "/travlog/images/avatar.jpg"
RELATIVE_URLS = False


MENUITEMS = (
    ("About", "/travlog/pages/about.html"),
    ("Archives", "/travlog/archives.html"),
    ("Categories", "/travlog/categories.html"),
    ("Tags", "/travlog/tags.html"),
)


FEED_ALL_ATOM = "feeds/all.atom.xml"
CATEGORY_FEED_ATOM = "feeds/{slug}.atom.xml"

EXTRA_PATH_METADATA = {
    "extra/CNAME": {"path": "CNAME"},
}

DELETE_OUTPUT_DIRECTORY = True

DISQUS_SITENAME = "lee-w-travlog"
GOOGLE_ANALYTICS = os.environ.get("GOOGLE_ANALYTICS")

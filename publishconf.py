#!/usr/bin/env python

import os
import sys

sys.path.append(os.curdir)
from pelicanconf import *  # noqa: F401, E402, F403
from pelicanconf import HOST

SITEURL = f"https://{HOST}"
STATIC_SITEURL = SITEURL
RELATIVE_URLS = False

FEED_MAX_ITEMS = 30
FEED_ALL_ATOM = "feeds/all.atom.xml"
CATEGORY_FEED_ATOM = "feeds/{slug}.atom.xml"

DELETE_OUTPUT_DIRECTORY = True

GOOGLE_ANALYTICS = os.environ.get("GOOGLE_ANALYTICS")
UMAMI_WEBSITE_ID = os.environ.get("UMAMI_WEBSITE_ID")

# local plugins
DEADLINKS_VALIDATION = False

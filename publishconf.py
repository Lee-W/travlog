import os
import sys

sys.path.append(os.curdir)
from pelicanconf import *
from pelicanconf import HOST

SITEURL = f"https://{HOST}"
STATIC_SITEURL = SITEURL
RELATIVE_URLS = False

# Keep the relative ARTICLE_LANG_URL from pelicanconf.py. Pelican prefixes it
# with the Japanese SITEURL when resolving article links; an absolute URL here
# would produce /ja/https://... links in both tables and database views.

FEED_MAX_ITEMS = 30
FEED_ALL_ATOM = "feeds/all.atom.xml"
CATEGORY_FEED_ATOM = "feeds/{slug}.atom.xml"

DELETE_OUTPUT_DIRECTORY = True
DRAFT_SAVE_AS = ""
DRAFT_URL = ""

UMAMI_WEBSITE_ID = os.environ.get("UMAMI_WEBSITE_ID")

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
# FEED_ATOM, not FEED_ALL_ATOM: the "all" feed also appends every article's
# translations, so a ja translation would show up in the zh feed (and a zh
# original in /ja/feeds/). Same path, so subscribers and <link> tags are kept.
FEED_ALL_ATOM = None
FEED_ATOM = "feeds/all.atom.xml"
CATEGORY_FEED_ATOM = "feeds/{slug}.atom.xml"

DELETE_OUTPUT_DIRECTORY = True
DRAFT_SAVE_AS = ""
DRAFT_URL = ""

UMAMI_WEBSITE_ID = os.environ.get("UMAMI_WEBSITE_ID")

import os
import sys

sys.path.append(os.curdir)
from pelicanconf import *
from pelicanconf import HOST

SITEURL = f"https://{HOST}"
STATIC_SITEURL = SITEURL
RELATIVE_URLS = False

# Built in pelicanconf.py against the development SITEURL; rebuild it so the
# Japanese subsite links to articles on the production site.
I18N_SUBSITES["ja"]["ARTICLE_LANG_URL"] = f"{SITEURL}/{ARTICLE_URL}"

FEED_MAX_ITEMS = 30
FEED_ALL_ATOM = "feeds/all.atom.xml"
CATEGORY_FEED_ATOM = "feeds/{slug}.atom.xml"

DELETE_OUTPUT_DIRECTORY = True
DRAFT_SAVE_AS = ""
DRAFT_URL = ""

UMAMI_WEBSITE_ID = os.environ.get("UMAMI_WEBSITE_ID")

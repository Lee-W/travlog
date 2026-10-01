import os
import sys

from pelican.plugins.i18n_feeds import feed_settings

sys.path.append(os.curdir)
from pelicanconf import *
from pelicanconf import HOST, I18N_SUBSITES, LANGUAGE_NAMES, SITENAME, SOCIAL

SITEURL = f"https://{HOST}"
STATIC_SITEURL = SITEURL
RELATIVE_URLS = False

# Keep the relative ARTICLE_LANG_URL from pelicanconf.py. Pelican prefixes it
# with the Japanese SITEURL when resolving article links; an absolute URL here
# would produce /ja/https://... links in both tables and database views.

FEED_MAX_ITEMS = 30
# feeds/ holds every language (pelican-i18n-feeds); each site's own language
# lives under its language prefix (zh-tw/feeds/ here, ja/feeds/ from the ja
# subsite). The helper also fixes the ja FEED_DOMAIN, sets attila's <head>
# feed link titles and points each site's RSS icon at its own feed.
globals().update(
    feed_settings(
        siteurl=SITEURL,
        sitename=SITENAME,
        default_lang=DEFAULT_LANG,
        subsites=I18N_SUBSITES,
        language_names=LANGUAGE_NAMES,
        all_languages_labels={
            "zh-tw": "全部語言 / All languages",
            "ja": "すべての言語 / All languages",
        },
        social=SOCIAL,
    )
)
# Feeds under /zh-tw/ and /ja/ get their own URL as <id>; feeds/ keeps
# Pelican's id, because subscribers already hold it.
I18N_FEEDS_URL_AS_ID = True
I18N_FEEDS_KEEP_ID_PREFIXES = ["feeds/"]

DELETE_OUTPUT_DIRECTORY = True
DRAFT_SAVE_AS = ""
DRAFT_URL = ""

UMAMI_WEBSITE_ID = os.environ.get("UMAMI_WEBSITE_ID")

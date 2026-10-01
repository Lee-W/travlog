import os
import sys

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
# feeds/ holds every language; each site's own language lives under its
# language prefix (zh-tw/feeds/ here, ja/feeds/ from the ja subsite).
# plugins/all_language_feeds.py writes feeds/: Pelican's FEED_ALL_ATOM only
# appends translations, so it would miss ja articles without a zh original.
FEED_ALL_ATOM = None
FEED_ATOM = "zh-tw/feeds/all.atom.xml"
CATEGORY_FEED_ATOM = "zh-tw/feeds/{slug}.atom.xml"
FEED_ALL_LANGUAGES_ATOM = "feeds/all.atom.xml"
# The old category feed URLs keep their subscribers and now carry every language.
CATEGORY_FEED_ALL_LANGUAGES_ATOM = "feeds/{slug}.atom.xml"


def _feed_links(sitename, lang, all_languages_label):
    """attila's <head> feed links: this language, every language, category."""
    titles = {
        "FEED_ATOM": f"{sitename} — {LANGUAGE_NAMES[lang]}",
        "CATEGORY_FEED_ATOM": f"{sitename} — {LANGUAGE_NAMES[lang]} — {{name}}",
    }
    extra = (
        (f"{sitename} — {all_languages_label}", f"{SITEURL}/{FEED_ALL_LANGUAGES_ATOM}"),
    )
    return {"FEED_LINK_TITLES": titles, "FEED_EXTRA_LINKS": extra}


def _social_with_rss(social, feed_url):
    """Point the header's RSS icon at this language's feed."""
    return tuple((name, feed_url if name == "RSS" else link) for name, link in social)


_zh_links = _feed_links(SITENAME, DEFAULT_LANG, "全部語言 / All languages")
FEED_LINK_TITLES = _zh_links["FEED_LINK_TITLES"]
FEED_EXTRA_LINKS = _zh_links["FEED_EXTRA_LINKS"]

# Copies, not in-place updates: pelicanconf.py's objects stay dev settings.
I18N_SUBSITES = {
    **I18N_SUBSITES,
    "ja": {
        **I18N_SUBSITES["ja"],
        # Pelican derives FEED_DOMAIN from the main SITEURL before the
        # subsite exists, so ja feed links and self links would miss /ja/.
        "FEED_DOMAIN": f"{SITEURL}/ja",
        "FEED_ATOM": "feeds/all.atom.xml",
        "CATEGORY_FEED_ATOM": "feeds/{slug}.atom.xml",
        "FEED_ALL_LANGUAGES_ATOM": None,
        "CATEGORY_FEED_ALL_LANGUAGES_ATOM": None,
        **_feed_links(
            I18N_SUBSITES["ja"]["SITENAME"], "ja", "すべての言語 / All languages"
        ),
        "SOCIAL": _social_with_rss(SOCIAL, f"{SITEURL}/ja/feeds/all.atom.xml"),
    },
}
SOCIAL = _social_with_rss(SOCIAL, f"{SITEURL}/{FEED_ATOM}")

DELETE_OUTPUT_DIRECTORY = True
DRAFT_SAVE_AS = ""
DRAFT_URL = ""

UMAMI_WEBSITE_ID = os.environ.get("UMAMI_WEBSITE_ID")

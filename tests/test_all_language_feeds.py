"""Build a two-language site with the publish feed settings and read the feeds.

pelican-i18n-feeds tests the plugin itself (ordering, FEED_MAX_ITEMS, three
languages); this checks that this blog's settings produce its feed layout.
"""

import json
import subprocess
import sys
from xml.etree import ElementTree

import pelicanconf
import publishconf

ATOM = {"atom": "http://www.w3.org/2005/Atom"}
FEED_KEYS = (
    "FEED_DOMAIN",
    "FEED_ALL_ATOM",
    "FEED_ATOM",
    "CATEGORY_FEED_ATOM",
    "FEED_ALL_LANGUAGES_ATOM",
    "CATEGORY_FEED_ALL_LANGUAGES_ATOM",
    "I18N_FEEDS_URL_AS_ID",
    "I18N_FEEDS_KEEP_ID_PREFIXES",
)
SITEURL = "https://example.com"


def _write_post(posts, name, lang, category, date="2026-01-01", body=""):
    suffix = "" if lang == "zh-tw" else f"-{lang}"
    (posts / f"{name}{suffix}.md").write_text(
        f"Title: {name} {lang}\nSlug: {name}\nLang: {lang}\nDate: {date}\n"
        f"Category: {category}\n\n{name} {lang}\n\n{body}\n",
        encoding="utf-8",
    )


def _build(tmp_path, write_posts):
    posts = tmp_path / "content" / "posts"
    posts.mkdir(parents=True)
    write_posts(posts)

    # Pelican derives FEED_DOMAIN from SITEURL, so drop the production value.
    ja_overrides = {
        key: value
        for key, value in publishconf.I18N_SUBSITES["ja"].items()
        if key in FEED_KEYS
    }
    ja_overrides["FEED_DOMAIN"] = f"{SITEURL}/ja"
    output = tmp_path / "output"
    settings = {
        "PATH": str(tmp_path / "content"),
        "OUTPUT_PATH": str(output),
        "SITEURL": SITEURL,
        "SITENAME": "Test",
        "AUTHOR": "Test",
        "TIMEZONE": "UTC",
        "DEFAULT_LANG": pelicanconf.DEFAULT_LANG,
        "DEFAULT_METADATA": pelicanconf.DEFAULT_METADATA,
        "THEME": "simple",
        "PLUGINS": [
            name
            for name in pelicanconf.PLUGINS
            if name in {"pelican.plugins.i18n_subsites", "pelican.plugins.i18n_feeds"}
        ],
        "STATIC_PATHS": [],
        "AUTHOR_FEED_ATOM": None,
        "AUTHOR_FEED_RSS": None,
        "TRANSLATION_FEED_ATOM": None,
        "FEED_MAX_ITEMS": publishconf.FEED_MAX_ITEMS,
        "I18N_UNTRANSLATED_ARTICLES": pelicanconf.I18N_UNTRANSLATED_ARTICLES,
        "I18N_SUBSITES": {"ja": ja_overrides},
        **{key: getattr(publishconf, key) for key in FEED_KEYS[1:]},
    }
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                # Pelican().run() sets up no logging: without a format, records
                # reach stderr without their level and the check below is moot.
                "import json, logging, sys; from pelican import Pelican; "
                "logging.basicConfig(format='%(levelname)s %(name)s: %(message)s'); "
                "from pelican.settings import read_settings; "
                "Pelican(read_settings(override=json.load(sys.stdin))).run()"
            ),
        ],
        input=json.dumps(settings),
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "WARNING" not in result.stdout + result.stderr
    return output


def _read_feed(path):
    root = ElementTree.parse(path).getroot()
    entries = [
        {
            "link": entry.find("atom:link", ATOM).get("href"),
            "id": entry.find("atom:id", ATOM).text,
            "published": entry.find("atom:published", ATOM).text,
            "content": (entry.find("atom:content", ATOM).text or ""),
        }
        for entry in root.findall("atom:entry", ATOM)
    ]
    self_link = next(
        link.get("href")
        for link in root.findall("atom:link", ATOM)
        if link.get("rel") == "self"
    )
    return {
        "id": root.find("atom:id", ATOM).text,
        "self": self_link,
        "entries": entries,
        "links": [entry["link"] for entry in entries],
    }


def _written_feeds(output):
    return sorted(
        path.relative_to(output).as_posix() for path in output.rglob("*.atom.xml")
    )


def _three_kinds_of_posts(posts):
    # A zh article with its ja translation, a ja article without a zh
    # original (linking to that translation), and a zh article without one.
    _write_post(posts, "review-post", "zh-tw", "Review", "2026-01-03")
    _write_post(posts, "review-post", "ja", "Review", "2026-01-03")
    _write_post(
        posts,
        "travel-post",
        "ja",
        "Travel",
        "2026-01-02",
        body="[review]({filename}review-post-ja.md)",
    )
    _write_post(posts, "cook-post", "zh-tw", "Cook", "2026-01-01")
    # Neither a draft nor a page belongs in a feed.
    (posts / "draft-post-ja.md").write_text(
        "Title: draft\nSlug: draft-post\nLang: ja\nDate: 2026-01-04\n"
        "Category: Travel\nStatus: draft\n\ndraft\n",
        encoding="utf-8",
    )
    pages = posts.parent / "pages"
    pages.mkdir()
    (pages / "about.md").write_text("Title: about\n\nabout\n", encoding="utf-8")


def test_feeds_split_by_language_with_every_article_in_feeds(tmp_path):
    output = _build(tmp_path, _three_kinds_of_posts)

    zh_review = f"{SITEURL}/review-post.html"
    ja_review = f"{SITEURL}/ja/review-post.html"
    ja_travel = f"{SITEURL}/ja/travel-post.html"
    zh_cook = f"{SITEURL}/cook-post.html"
    # Newest first; the two review-post versions share a date.
    expected = {
        "feeds/all.atom.xml": [zh_review, ja_review, ja_travel, zh_cook],
        "feeds/review.atom.xml": [zh_review, ja_review],
        "feeds/travel.atom.xml": [ja_travel],
        "feeds/cook.atom.xml": [zh_cook],
        "zh-tw/feeds/all.atom.xml": [zh_review, zh_cook],
        "zh-tw/feeds/review.atom.xml": [zh_review],
        "zh-tw/feeds/cook.atom.xml": [zh_cook],
        "ja/feeds/all.atom.xml": [ja_review, ja_travel],
        "ja/feeds/review.atom.xml": [ja_review],
        "ja/feeds/travel.atom.xml": [ja_travel],
    }
    assert _written_feeds(output) == sorted(expected)

    feeds = {path: _read_feed(output / path) for path in expected}
    assert {path: feed["links"] for path, feed in feeds.items()} == expected
    for path, feed in feeds.items():
        assert feed["self"] == f"{SITEURL}/{path}"
        if path.startswith("feeds/"):
            # Existing subscribers keep the id Pelican always wrote: the site URL.
            assert feed["id"] == f"{SITEURL}/"
        else:
            assert feed["id"] == feed["self"]

    # The ja-only article is the same entry in the main and the ja feeds, and
    # its relative link resolves to the ja subsite in both.
    main_entry = feeds["feeds/all.atom.xml"]["entries"][2]
    ja_entry = feeds["ja/feeds/all.atom.xml"]["entries"][1]
    assert main_entry == ja_entry
    assert f'href="{ja_review}"' in main_entry["content"]


def test_publishconf_gives_each_site_its_own_feed_links():
    ja = publishconf.I18N_SUBSITES["ja"]
    site = publishconf.SITEURL

    assert ja["FEED_DOMAIN"] == f"{site}/ja"
    assert dict(ja["SOCIAL"])["RSS"] == f"{site}/ja/feeds/all.atom.xml"
    assert dict(publishconf.SOCIAL)["RSS"] == f"{site}/zh-tw/feeds/all.atom.xml"
    keys = {"FEED_ATOM", "CATEGORY_FEED_ATOM"}
    assert set(ja["FEED_LINK_TITLES"]) == set(publishconf.FEED_LINK_TITLES) == keys
    assert ja["FEED_LINK_TITLES"] != publishconf.FEED_LINK_TITLES
    all_languages = f"{site}/feeds/all.atom.xml"
    assert ja["FEED_EXTRA_LINKS"][0][1] == all_languages
    assert publishconf.FEED_EXTRA_LINKS[0][1] == all_languages
    # The dev settings keep no production feed domain.
    assert "FEED_DOMAIN" not in pelicanconf.I18N_SUBSITES["ja"]

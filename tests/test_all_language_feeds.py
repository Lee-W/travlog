"""Build a two-language site with the publish feed settings and read the feeds."""

import json
import subprocess
import sys
from pathlib import Path
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
            if name in {"pelican.plugins.i18n_subsites", "all_language_feeds"}
        ],
        "PLUGIN_PATHS": [str(Path(__file__).resolve().parents[1] / "plugins")],
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
                "import json, sys; from pelican import Pelican; "
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


def test_articles_with_the_same_date_keep_the_site_order(tmp_path):
    def write_posts(posts):
        # ja-only names sort before the zh ones, so reading order cannot
        # produce the expected order by accident.
        for index in range(4):
            _write_post(posts, f"z-zh-{index}", "zh-tw", "Travel")
            _write_post(posts, f"a-ja-{index}", "ja", "Travel")
        _write_post(posts, "m-both", "zh-tw", "Travel")
        _write_post(posts, "m-both", "ja", "Travel")

    output = _build(tmp_path, write_posts)

    links = _read_feed(output / "feeds/all.atom.xml")["links"]
    site = {f"{SITEURL}/z-zh-{index}.html" for index in range(4)}
    site.add(f"{SITEURL}/m-both.html")
    # Site articles first (in the site's order), then translations, then the
    # articles only another subsite publishes, by file path.
    assert set(links[:5]) == site
    assert links[5:] == [f"{SITEURL}/ja/m-both.html"] + [
        f"{SITEURL}/ja/a-ja-{index}.html" for index in range(4)
    ]


def test_all_language_feeds_keep_the_newest_items_up_to_the_limit(tmp_path):
    limit = publishconf.FEED_MAX_ITEMS

    def write_posts(posts):
        # Interleave the languages: even days in zh, odd days ja-only.
        for day in range(1, limit + 6):
            lang = "zh-tw" if day % 2 == 0 else "ja"
            date = f"2026-03-{day:02d}" if day <= 31 else f"2026-04-{day - 31:02d}"
            _write_post(posts, f"post-{day:02d}", lang, "Travel", date)

    output = _build(tmp_path, write_posts)

    for path in ("feeds/all.atom.xml", "feeds/travel.atom.xml"):
        entries = _read_feed(output / path)["entries"]
        published = [entry["published"] for entry in entries]
        assert len(entries) == limit
        assert len({entry["link"] for entry in entries}) == limit
        assert published == sorted(published, reverse=True)
        # The oldest posts fall off: post-01 .. post-05.
        slugs = {entry["link"].rsplit("/", 1)[1] for entry in entries}
        assert slugs == {f"post-{day:02d}.html" for day in range(6, limit + 6)}
        assert any("/ja/" in entry["link"] for entry in entries)
        assert any("/ja/" not in entry["link"] for entry in entries)


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

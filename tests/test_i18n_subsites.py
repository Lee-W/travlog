"""Exercise the site's language overrides in an isolated Pelican process."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

import pelicanconf


@pytest.mark.parametrize("has_japanese_articles", [False, True])
def test_subsites_generate_pages_and_random_entries(tmp_path, has_japanese_articles):
    content = tmp_path / "content"
    pages = content / "pages"
    posts = content / "posts"
    pages.mkdir(parents=True)
    posts.mkdir()
    for slug in ("blogroll", "about"):
        for lang in ("zh-tw", "ja"):
            suffix = {"zh-tw": "", "en": "-en", "ja": "-ja"}[lang]
            (pages / f"{slug}{suffix}.md").write_text(
                f"Title: {slug} {lang}\nSlug: {slug}\nLang: {lang}\n\n{slug} {lang}\n",
                encoding="utf-8",
            )
    article_languages = ("zh-tw", "ja") if has_japanese_articles else ("zh-tw",)
    for lang in article_languages:
        (posts / f"post-{lang}.md").write_text(
            f"Title: Article {lang}\nSlug: article-{lang}\nLang: {lang}\n"
            "Date: 2026-01-01\nCategory: Test\n\nArticle body.\n",
            encoding="utf-8",
        )

    output = tmp_path / "output"
    settings = {
        "PATH": str(content),
        "OUTPUT_PATH": str(output),
        "SITEURL": "https://example.com",
        "SITENAME": "Test",
        "AUTHOR": "Test",
        "TIMEZONE": "UTC",
        "DEFAULT_LANG": pelicanconf.DEFAULT_LANG,
        "THEME": "simple",
        "THEME_TEMPLATES_OVERRIDES": [
            str(Path(__file__).resolve().parents[1] / "theme-overrides")
        ],
        "PLUGINS": [
            name
            for name in pelicanconf.PLUGINS
            if name in {"pelican.plugins.i18n_subsites", "random_article_subsites"}
        ],
        "PLUGIN_PATHS": [str(Path(__file__).resolve().parents[1] / "plugins")],
        "STATIC_PATHS": [],
        "FEED_ALL_ATOM": None,
        "CATEGORY_FEED_ATOM": None,
        "AUTHOR_FEED_ATOM": None,
        "PAGE_URL": "pages/{slug}.html",
        "PAGE_SAVE_AS": "pages/{slug}.html",
        "I18N_UNTRANSLATED_ARTICLES": pelicanconf.I18N_UNTRANSLATED_ARTICLES,
        "I18N_UNTRANSLATED_PAGES": pelicanconf.I18N_UNTRANSLATED_PAGES,
        "I18N_SUBSITES": {
            lang: {
                key: value
                for key, value in overrides.items()
                if key in {"LOCALE", "RANDOM_ARTICLE_FALLBACK_URL"}
            }
            for lang, overrides in pelicanconf.I18N_SUBSITES.items()
        },
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
        timeout=30,
    )
    log = result.stdout + result.stderr
    assert result.returncode == 0, log
    assert "original (not translated)" not in log
    assert "No published articles found" not in log

    for lang, prefix in (("zh-tw", ""), ("ja", "ja")):
        site = output / prefix
        about = (site / "pages/about.html").read_text(encoding="utf-8")
        assert f"about {lang}" in about
        for slug in ("blogroll",):
            page = site / f"pages/{slug}.html"
            assert f"{slug} {lang}" in page.read_text(encoding="utf-8")
        random_page = site / "random/index.html"
        random_html = random_page.read_text(encoding="utf-8")
        if lang == "ja" and not has_japanese_articles:
            assert '<html lang="ja">' in random_html
            assert 'http-equiv="refresh" content="0; url=/random/"' in random_html
            assert '<a href="/random/">' in random_html
        else:
            assert f"article-{lang}.html" in random_html
            for other_lang in set(article_languages) - {lang}:
                assert f"article-{other_lang}.html" not in random_html

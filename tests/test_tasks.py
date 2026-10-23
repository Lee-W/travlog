import re
from textwrap import dedent

import tasks
from tasks import _create_post_from_template


def test_create_post_from_template_uses_unprefixed_filename(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "draft.md").write_text(
        dedent("""\
            Title: $title
            Date: $date
            Category: $category
            Tags:
            Slug: $slug
            Cover:
            Authors: Wei Lee
            Lang: $lang
            Status: draft

            [intro]

            <!--more-->

            ##"""),
        encoding="utf-8",
    )

    _create_post_from_template(
        "draft.md",
        "Sample Title",
        "Travel",
        "sample-title",
        {"lang": "zh-tw"},
    )

    created = next((tmp_path / "content" / "posts" / "travel").rglob("sample-title.md"))
    assert created.name == "sample-title.md"
    assert not created.name[0].isdigit()
    assert "Status: draft" in created.read_text(encoding="utf-8")


def test_create_post_from_template_stamps_japan_time(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "draft.md").write_text("Date: $date\nSlug: $slug\n", encoding="utf-8")

    _create_post_from_template("draft.md", "Sample Title", "Travel", "sample-title")

    created = next((tmp_path / "content" / "posts" / "travel").rglob("sample-title.md"))
    date_line = created.read_text(encoding="utf-8").splitlines()[0]
    assert re.fullmatch(r"Date: \d{4}-\d{2}-\d{2} \d{2}:\d{2} \+0900", date_line)


def _page(body: str, *, canonical: str, menu: str = "") -> str:
    return (
        '<html lang="zh-tw"><head>'
        f'<link rel="canonical" href="https://travlog.wei-lee.me{canonical}">'
        f'</head><body><ul id="nav-language-menu">{menu}</ul>{body}</body></html>'
    )


def _write(root, relative: str, content: str):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_fix_internal_links_rewrites_broken_links(tmp_path, monkeypatch):
    output = tmp_path / "output"
    monkeypatch.setitem(tasks.CONFIG, "deploy_path", str(output))
    menu = (
        '<li><a href="/category/cook.html" data-fallback="/">zh</a></li>'
        '<li><a href="/ja/category/cook.html" data-fallback="/ja/">ja</a></li>'
    )
    page = _write(
        output,
        "category/cook.html",
        _page(
            '<a id="tag" href="/ja/tag/missing.html">t</a>'
            '<a id="ok" href="/pages/about.html">a</a>'
            '<a id="article" href="/posts/review/x">p</a>'
            '<a id="ext" href="https://example.com/nope.html">e</a>',
            canonical="/category/cook.html",
            menu=menu,
        ),
    )
    _write(output, "pages/about.html", "<html></html>")
    _write(output, "posts/review/x/index.html", "<html></html>")

    tasks._fix_internal_links()

    html = page.read_text(encoding="utf-8")
    assert 'href="/ja/"' in html  # missing translation -> data-fallback
    assert 'href="/ja/" id="tag"' in html  # tag page -> subsite home
    assert "/ja/category/cook.html" not in html
    assert 'href="/pages/about.html"' in html  # existing target untouched
    assert 'href="/posts/review/x"' in html  # directory-style article untouched
    assert 'href="https://example.com/nope.html"' in html  # external untouched


def test_fix_internal_links_adds_hreflang_only_for_real_translations(
    tmp_path, monkeypatch
):
    output = tmp_path / "output"
    monkeypatch.setitem(tasks.CONFIG, "deploy_path", str(output))
    translated = _write(
        output,
        "pages/about.html",
        _page(
            "",
            canonical="/pages/about.html",
            menu=(
                '<li><a href="/pages/about.html">zh</a></li>'
                '<li><a href="/ja/pages/about.html">ja</a></li>'
            ),
        ),
    )
    _write(output, "ja/pages/about.html", "<html></html>")
    untranslated = _write(
        output,
        "posts/review/x/index.html",
        _page(
            "",
            canonical="/posts/review/x",
            menu=(
                '<li><a href="/posts/review/x">zh</a></li>'
                '<li><a href="/ja/posts/review/x" data-fallback="/ja/">ja</a></li>'
            ),
        ),
    )

    tasks._fix_internal_links()

    html = translated.read_text(encoding="utf-8")
    assert 'hreflang="zh-TW"' in html
    assert 'hreflang="ja"' in html
    assert 'hreflang="x-default"' in html
    assert "https://travlog.wei-lee.me/ja/pages/about.html" in html
    assert "hreflang" not in untranslated.read_text(encoding="utf-8")


def test_normalize_sitemap_removes_duplicate_urls(tmp_path):
    sitemap = tmp_path / "sitemap.xml"
    sitemap.write_text(
        '<?xml version="1.0" encoding="utf-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        "<url><loc>https://travlog.wei-lee.me/pages/about.html</loc></url>"
        "<url><loc>https://travlog.wei-lee.me/archives.html</loc></url>"
        "<url><loc>https://travlog.wei-lee.me/pages/about.html</loc></url>"
        "</urlset>",
        encoding="utf-8",
    )

    assert tasks._normalize_sitemap(sitemap) == 1

    content = sitemap.read_text(encoding="utf-8")
    assert content.count("pages/about.html") == 1
    assert content.count("archives.html") == 1
    assert tasks._normalize_sitemap(tmp_path / "missing.xml") == 0

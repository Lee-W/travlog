import re
from textwrap import dedent

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

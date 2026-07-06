from tasks import _create_post_from_template


def test_create_post_from_template_uses_unprefixed_filename(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "draft.md").write_text(
        "\n".join(
            [
                "Title: $title",
                "Date: $date",
                "Category: $category",
                "Tags:",
                "Slug: $slug",
                "Cover:",
                "Authors: Wei Lee",
                "Lang: $lang",
                "Status: draft",
                "",
                "[intro]",
                "",
                "<!--more-->",
                "",
                "##",
            ]
        ),
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

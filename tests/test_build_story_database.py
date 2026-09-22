import json
from copy import deepcopy

import pytest
import yaml
from bs4 import BeautifulSoup
from pelican.plugins.tabular.views import render_view

from scripts.build_story_database import CATEGORIES, build_database, view_config


@pytest.fixture
def ranking_dir(tmp_path):
    for category in CATEGORIES:
        (tmp_path / f"{category}.yaml").write_text("[]\n", encoding="utf-8")
    return tmp_path


def test_keeps_same_title_entries_ranks_and_review_links(ranking_dir):
    reviews = [
        {
            "text": "2026 春",
            "href": "{filename}/posts/review/2026/example.md",
            "season_href": "{filename}/posts/review/2026/season.md#example",
        }
    ]
    entries = [
        {"title": "同名作品", "tier": "SS", "reviews": reviews},
        {"title": "同名作品", "tier": "A"},
    ]
    path = ranking_dir / "anime.yaml"
    path.write_text(yaml.safe_dump(entries, allow_unicode=True), encoding="utf-8")
    before = path.read_bytes()
    rows = build_database(ranking_dir)
    assert [
        (row["title"], row["tier"], row["rank"], row["has_review"]) for row in rows
    ] == [
        ("同名作品", "SS", 9, "yes"),
        ("同名作品", "A", 7, "no"),
    ]
    assert rows[0]["reviews"] == reviews
    assert path.read_bytes() == before


@pytest.mark.parametrize("category", ["star-wars", "artbook"])
def test_missing_tier_is_not_invented(ranking_dir, category):
    (ranking_dir / f"{category}.yaml").write_text(
        "- title: Untiered work\n  group: Movie\n", encoding="utf-8"
    )
    row = build_database(ranking_dir)[0]
    assert (row["tier"], row["rank"]) == ("unranked", None)
    assert "status" not in row


@pytest.mark.parametrize("change", ["missing", "unknown"])
def test_category_changes_fail_instead_of_silently_dropping_works(ranking_dir, change):
    if change == "missing":
        (ranking_dir / "anime.yaml").unlink()
    else:
        (ranking_dir / "new-category.yaml").write_text("[]\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Ranking categories changed"):
        build_database(ranking_dir)


@pytest.mark.parametrize(("lang", "displayed"), [("zh-tw", "聲之形"), ("ja", "聲の形")])
def test_localized_views_keep_both_titles_searchable(ranking_dir, lang, displayed):
    """One config serves both languages; the plugin translates per component.

    `title` is projected from `translations.ja.title`, so both
    spellings must stay in the search index either way, and the generated
    rows must not mutate the database the other subsite renders from.
    """
    (ranking_dir / "anime.yaml").write_text(
        "- title: 聲之形\n  translations:\n    ja:\n      title: 聲の形\n  tier: SSS\n",
        encoding="utf-8",
    )
    original = build_database(ranking_dir)
    rows = deepcopy(original)
    html = render_view(rows, view_config(), table_id="works", lang=lang)
    payload = json.loads(
        BeautifulSoup(html, "html.parser").select_one(".tabular-data").string
    )
    record = payload["records"][0]
    assert record["values"]["title"] == [displayed]
    assert "聲之形" in record["search"]
    assert "聲の形" in record["search"]
    assert rows == original
    assert original[0]["title"] == "聲之形"


def test_unknown_tier_stops_generation(ranking_dir):
    (ranking_dir / "anime.yaml").write_text("- title: Example\n  tier: typo\n")
    with pytest.raises(ValueError, match="unknown tier"):
        build_database(ranking_dir)


@pytest.mark.parametrize(
    ("translations", "lang", "displayed"),
    [
        pytest.param({"ja": {"title": ""}}, "ja", [""], id="explicit-empty"),
        pytest.param(
            {"en": {"title": "A Silent Voice"}},
            "en",
            ["A Silent Voice"],
            id="other-language",
        ),
        pytest.param(
            {"ja-JP": {"title": "聲の形"}}, "ja-JP", ["聲の形"], id="regional-language"
        ),
        pytest.param({}, "ja", ["聲之形"], id="missing-translation"),
    ],
)
def test_catalog_preserves_translations_for_display(
    ranking_dir, translations, lang, displayed
):
    path = ranking_dir / "anime.yaml"
    path.write_text(
        yaml.safe_dump(
            [{"title": "聲之形", "translations": translations}], allow_unicode=True
        )
    )
    before = path.read_bytes()
    rows = build_database(ranking_dir)
    assert rows[0]["translations"] == translations
    original = deepcopy(rows)
    html = render_view(rows, view_config(), table_id="works", lang=lang)
    payload = json.loads(
        BeautifulSoup(html, "html.parser").select_one(".tabular-data").string
    )
    assert payload["records"][0]["values"]["title"] == displayed
    assert rows == original
    assert path.read_bytes() == before

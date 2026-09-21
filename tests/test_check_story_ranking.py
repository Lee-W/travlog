from pathlib import Path

from scripts.build_story_database import CATEGORIES
from scripts.check_story_ranking import check_page_references, check_yaml_file


def _make_review_dir(tmp_path: Path) -> tuple[Path, Path]:
    review_dir = tmp_path / "content/posts/review/2025"
    review_dir.mkdir(parents=True)
    yaml_path = tmp_path / "anime.yaml"
    return review_dir, yaml_path


def _write_season(review_dir: Path) -> Path:
    path = review_dir / "02-what-i-watched-in-2025-spring.md"
    path.write_text("## 動畫\n\n### 測試作品\n", encoding="utf-8")
    return path


def test_direct_review_with_seasonal_backlink(tmp_path):
    review_dir, yaml_path = _make_review_dir(tmp_path)
    season = _write_season(review_dir)
    direct = review_dir / "01-example.md"
    direct.write_text(
        "心得\n\n同季還看了什麼："
        "[2025 春季看什麼]"
        "({filename}/posts/review/2025/02-what-i-watched-in-2025-spring.md#_2)\n",
        encoding="utf-8",
    )
    yaml_path.write_text(
        "- title: 測試作品\n"
        "  reviews:\n"
        "  - text: 2025 春\n"
        "    href: '{filename}/posts/review/2025/01-example.md'\n"
        "    season_href: "
        "'{filename}/posts/review/2025/02-what-i-watched-in-2025-spring.md#_2'\n",
        encoding="utf-8",
    )

    errors = check_yaml_file(yaml_path, tmp_path, {})

    assert errors == [], season


def test_direct_review_requires_seasonal_backlink(tmp_path):
    review_dir, yaml_path = _make_review_dir(tmp_path)
    _write_season(review_dir)
    (review_dir / "01-example.md").write_text("心得\n", encoding="utf-8")
    yaml_path.write_text(
        "- title: 測試作品\n"
        "  reviews:\n"
        "  - text: 2025 春\n"
        "    href: '{filename}/posts/review/2025/01-example.md'\n"
        "    season_href: "
        "'{filename}/posts/review/2025/02-what-i-watched-in-2025-spring.md#_2'\n",
        encoding="utf-8",
    )

    errors = check_yaml_file(yaml_path, tmp_path, {})

    assert any("lacks seasonal backlink" in error for error in errors)


def test_combined_view_checks_all_canonical_sources(tmp_path):
    sources = tmp_path / "sources"
    sources.mkdir()
    for category in CATEGORIES:
        (sources / f"{category}.yaml").write_text("[]\n")
    page = tmp_path / "story-ranking.md"
    page.write_text('{% table data/story-database.yaml view="works" id="works" %}')
    assert check_page_references(sources, page) == []
    (sources / "anime.yaml").unlink()
    (sources / "new.yaml").write_text("[]\n")
    errors = check_page_references(sources, page)
    assert any("orphan YAML: new.yaml" in error for error in errors)
    assert any(
        "dangling reference" in error and "anime.yaml" in error for error in errors
    )


def test_mentioning_catalog_without_rendering_it_does_not_cover_sources(tmp_path):
    (tmp_path / "anime.yaml").write_text("[]\n")
    page = tmp_path / "story-ranking.md"
    page.write_text("Data comes from data/story-database.yaml")
    assert any(
        "orphan YAML: anime.yaml" in error
        for error in check_page_references(tmp_path, page)
    )

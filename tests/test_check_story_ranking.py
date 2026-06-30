from pathlib import Path

from scripts.check_story_ranking import check_yaml_file


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

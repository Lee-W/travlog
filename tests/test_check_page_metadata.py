from pathlib import Path

from scripts.check_page_metadata import check_file


def write_page(tmp_path: Path, metadata: str) -> Path:
    page = tmp_path / "page.md"
    page.write_text(f"{metadata}\n\nContent\n", encoding="utf-8")
    return page


def test_accepts_complete_page_metadata(tmp_path):
    page = write_page(
        tmp_path,
        "\n".join(
            [
                "Title: Page",
                "Date: 2026-07-10 11:33 +0800",
                "Modified: 2026-07-10 11:33 +0800",
                "Slug: page",
                "Summary: A useful page.",
            ]
        ),
    )

    assert check_file(page) == []


def test_reports_missing_and_misordered_metadata(tmp_path):
    page = write_page(
        tmp_path,
        "\n".join(
            [
                "Title: Page",
                "Slug: page",
                "Date: 2026-07-10",
                "Summary: A useful page.",
            ]
        ),
    )

    errors = check_file(page)

    assert "  missing required field 'Modified'" in errors
    assert any("invalid Date" in error for error in errors)
    assert any("fields out of order" in error for error in errors)

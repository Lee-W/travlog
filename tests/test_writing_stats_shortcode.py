"""Integration test for the pelican-stat writing-stats shortcode."""

from pathlib import Path

from pelican import Pelican
from pelican.settings import read_settings

REPO_ROOT = Path(__file__).resolve().parent.parent
PELICANCONF_PATH = REPO_ROOT / "pelicanconf.py"

SHORTCODE_LITERAL = "{% writing_stats %}"
WIDGET_MARKER = '<div class="pelican-stat-widget">'


def test_writing_stats_shortcode_is_substituted(tmp_path):
    settings = read_settings(
        path=str(PELICANCONF_PATH),
        override={
            "OUTPUT_PATH": str(tmp_path),
            "ARTICLE_PATHS": [],
            "STATIC_PATHS": [],
        },
    )
    Pelican(settings).run()

    html_path = tmp_path / "pages/about.html"
    assert html_path.exists(), f"expected build output at {html_path}"
    html = html_path.read_text(encoding="utf-8")

    assert SHORTCODE_LITERAL not in html
    assert WIDGET_MARKER in html

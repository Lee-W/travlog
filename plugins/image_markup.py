"""Add browser-friendly attributes to generated article images."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import unquote, urlparse
import warnings

from bs4 import BeautifulSoup
from pelican import signals
from PIL import Image, UnidentifiedImageError

_content_root = Path("content").resolve()


def _initialize(pelican) -> None:
    global _content_root
    _content_root = Path(pelican.settings["PATH"]).resolve()


def _source_image(src: str) -> Path | None:
    url_path = unquote(urlparse(src).path)
    if not url_path.startswith("/images/"):
        return None
    return _content_root / url_path.removeprefix("/")


def _add_image_markup(path: str, context: dict) -> None:
    output = Path(path)
    if output.suffix.lower() != ".html":
        return

    html = output.read_text(encoding="utf-8")
    if 'class="post-content"' not in html or "<img" not in html:
        return

    soup = BeautifulSoup(html, "html.parser")
    changed = False
    for image in soup.select(".post-content img"):
        if not image.get("loading"):
            image["loading"] = "lazy"
            changed = True
        if not image.get("decoding"):
            image["decoding"] = "async"
            changed = True

        source = _source_image(image.get("src", ""))
        if source is None or not source.is_file():
            continue
        if image.get("width") and image.get("height"):
            continue
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", Image.DecompressionBombWarning)
                with Image.open(source) as source_image:
                    width, height = source_image.size
        except (OSError, UnidentifiedImageError):
            continue
        image["width"] = str(width)
        image["height"] = str(height)
        changed = True

    if changed:
        output.write_text(str(soup), encoding="utf-8")


def register() -> None:
    signals.initialized.connect(_initialize)
    signals.content_written.connect(_add_image_markup)

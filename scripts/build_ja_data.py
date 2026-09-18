"""Generate the Japanese subsite's data from the main data files.

`content/data/**` holds Taiwanese Mandarin work titles in `title`, plus the
original title in `title_native` where one is known. The Japanese subsite wants
the original first, so this writes a parallel tree where `title` is the native
title when there is one and the Taiwanese Mandarin title otherwise.

`pelicanconf.py` points the subsite at this tree with `TABULAR_DATA_ROOT`, so
the `.md` pages keep the same `{% table data/... %}` calls in both languages.

The output is generated at build time and is not committed — run it through
`inv build` / `inv rebuild` / `inv build-publish`, which call it automatically.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import Any

import yaml

SOURCE = Path("content/data")
TARGET = Path(".ja-data/data")
PLACES_SOURCE = Path("content/places")
PLACES_TARGET = Path(".ja-data/places")

# Place names as they appear in content/places/**, mapped to how they are
# written in Japanese. Only the values that actually differ are listed; every
# other value in the data (東京, 京都, London, …) is already correct.
PLACE_NAMES = {
    # country
    "臺灣": "台湾",
    "英國": "イギリス",
    "德國": "ドイツ",
    "美國": "アメリカ",
    "菲律賓": "フィリピン",
    # city
    "臺北市": "台北市",
    "臺北": "台北",
    "臺南市": "台南市",
    "臺中市": "台中市",
    "苗栗縣": "苗栗県",
    "廣島": "広島",
    "橫濱": "横浜",
    "靜岡": "静岡",
    "達沃": "ダバオ",
    # district
    "松山區": "松山区",
    "大安區": "大安区",
    "中正區": "中正区",
    "大同區": "大同区",
    "信義區": "信義区",
    "中山區": "中山区",
    "中西區": "中西区",
    "南港區": "南港区",
    "仁愛區": "仁愛区",
    "南區": "南区",
    "北區": "北区",
    "東區": "東区",
    "歸仁區": "帰仁区",
    "新莊區": "新荘区",
    "林口區": "林口区",
    "士林區": "士林区",
    "萬華區": "万華区",
    "萬華": "万華",
    "三義鄉": "三義郷",
}
PLACE_FIELDS = ("country", "city", "district", "state", "region")


def localize(rows: Any) -> tuple[Any, int]:
    """Promote `title_native` into `title`; return the rows and how many moved."""
    if not isinstance(rows, list):
        return rows, 0
    swapped = 0
    for row in rows:
        if not isinstance(row, dict):
            continue
        native = row.pop("title_native", None)
        if native:
            row["title"] = native
            swapped += 1
    return rows, swapped


def localize_places(node: Any) -> int:
    """Rewrite place-name fields in place; return how many values changed."""
    changed = 0
    if isinstance(node, dict):
        for field in PLACE_FIELDS:
            value = node.get(field)
            if isinstance(value, str) and value.strip() in PLACE_NAMES:
                node[field] = PLACE_NAMES[value.strip()]
                changed += 1
        for value in node.values():
            changed += localize_places(value)
    elif isinstance(node, list):
        for value in node:
            changed += localize_places(value)
    return changed


def copy_tree(source: Path, target: Path, transform) -> tuple[int, int]:
    """Mirror `source` into `target`, running `transform` over each YAML doc."""
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    files = touched = 0
    for source_path in sorted(source.rglob("*")):
        if source_path.is_dir():
            continue
        target_path = target / source_path.relative_to(source)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        if source_path.suffix.lower() not in (".yaml", ".yml"):
            shutil.copy2(source_path, target_path)
            continue
        document = yaml.safe_load(source_path.read_text(encoding="utf-8"))
        touched += transform(document)
        target_path.write_text(
            yaml.safe_dump(document, allow_unicode=True, sort_keys=False, width=10**6),
            encoding="utf-8",
        )
        files += 1
    return files, touched


def main() -> int:
    if not SOURCE.is_dir() or not PLACES_SOURCE.is_dir():
        print(f"{SOURCE} or {PLACES_SOURCE} not found", file=sys.stderr)
        return 1

    def promote_titles(document: Any) -> int:
        _, swapped = localize(document)
        return swapped

    data_files, swapped = copy_tree(SOURCE, TARGET, promote_titles)
    place_files, renamed = copy_tree(PLACES_SOURCE, PLACES_TARGET, localize_places)

    print(
        f"ja data: {data_files} data files ({swapped} native titles promoted), "
        f"{place_files} place files ({renamed} place names localized)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

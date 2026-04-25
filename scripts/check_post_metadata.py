#!/usr/bin/env python3
"""Check Pelican post metadata style consistency."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REQUIRED_FIELDS = ["Title", "Date", "Category", "Tags", "Slug", "Authors"]
FIELD_ORDER = [
    "Title",
    "Subtitle",
    "Date",
    "Category",
    "Tags",
    "Slug",
    "Series",
    "Cover",
    "Authors",
    "Lang",
]
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2} \+\d{4}$")
SLUG_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]$|^[a-zA-Z0-9]$")
VALID_LANGS = {"zh-tw", "en"}


def parse_metadata(path: Path) -> tuple[dict[str, str], list[str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    metadata: dict[str, str] = {}
    order: list[str] = []
    for line in lines:
        if not line.strip():
            break
        if ":" in line:
            key, _, value = line.partition(":")
            metadata[key.strip()] = value.strip()
            order.append(key.strip())
    return metadata, order


def check_file(path: Path, valid_categories: list[str]) -> list[str]:
    errors: list[str] = []
    try:
        metadata, order = parse_metadata(path)
    except Exception as e:
        return [f"  failed to parse metadata: {e}"]

    for field in REQUIRED_FIELDS:
        if field not in metadata:
            errors.append(f"  missing required field '{field}'")

    if "Date" in metadata and not DATE_PATTERN.match(metadata["Date"]):
        errors.append(
            f"  invalid Date '{metadata['Date']}' (expected YYYY-MM-DD HH:MM +NNNN)"
        )

    if "Authors" in metadata and metadata["Authors"] != "Wei Lee":
        errors.append(f"  Authors must be 'Wei Lee', got '{metadata['Authors']}'")

    if "Slug" in metadata and not SLUG_PATTERN.match(metadata["Slug"]):
        errors.append(
            f"  Slug must be alphanumeric with hyphens, got '{metadata['Slug']}'"
        )

    if (
        valid_categories
        and "Category" in metadata
        and metadata["Category"] not in valid_categories
    ):
        errors.append(
            f"  Category '{metadata['Category']}' not in {valid_categories}"
        )

    if "Lang" in metadata and metadata["Lang"] not in VALID_LANGS:
        errors.append(
            f"  Lang must be one of {sorted(VALID_LANGS)}, got '{metadata['Lang']}'"
        )

    known_present = [f for f in FIELD_ORDER if f in order]
    actual_known = [f for f in order if f in FIELD_ORDER]
    if actual_known != known_present:
        errors.append(
            f"  fields out of order\n"
            f"    expected: {known_present}\n"
            f"    got:      {actual_known}"
        )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="*")
    parser.add_argument(
        "--categories", default="", help="comma-separated list of valid categories"
    )
    args = parser.parse_args()

    valid_categories = [c.strip() for c in args.categories.split(",") if c.strip()]
    failed = False

    for filename in args.files:
        path = Path(filename)
        errors = check_file(path, valid_categories)
        if errors:
            print(f"{path}:")
            for error in errors:
                print(error)
            failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

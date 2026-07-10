#!/usr/bin/env python3
"""Check Pelican static-page metadata style consistency."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REQUIRED_FIELDS = ["Title", "Date", "Modified", "Slug", "Summary"]
FIELD_ORDER = [
    "Title",
    "Date",
    "Modified",
    "Slug",
    "Summary",
    "Lang",
    "Status",
    "Save_as",
    "URL",
]
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2} \+\d{4}$")
SLUG_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]$|^[a-zA-Z0-9]$")
VALID_LANGS = {"zh-tw", "en"}
VALID_STATUSES = {"hidden"}


def parse_metadata(path: Path) -> tuple[dict[str, str], list[str]]:
    metadata: dict[str, str] = {}
    order: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            break
        if ":" in line:
            key, _, value = line.partition(":")
            metadata[key.strip()] = value.strip()
            order.append(key.strip())
    return metadata, order


def check_file(path: Path) -> list[str]:
    metadata, order = parse_metadata(path)
    errors: list[str] = []

    for field in REQUIRED_FIELDS:
        if not metadata.get(field):
            errors.append(f"  missing required field '{field}'")

    for field in ("Date", "Modified"):
        value = metadata.get(field)
        if value and not DATE_PATTERN.match(value):
            errors.append(
                f"  invalid {field} '{value}' (expected YYYY-MM-DD HH:MM +NNNN)"
            )

    slug = metadata.get("Slug")
    if slug and not SLUG_PATTERN.match(slug):
        errors.append(f"  invalid Slug '{slug}'")

    lang = metadata.get("Lang")
    if lang and lang not in VALID_LANGS:
        errors.append(f"  Lang must be one of {sorted(VALID_LANGS)}, got '{lang}'")

    status = metadata.get("Status")
    if status and status.lower() not in VALID_STATUSES:
        errors.append(
            f"  Status must be one of {sorted(VALID_STATUSES)}, got '{status}'"
        )

    known_present = [field for field in FIELD_ORDER if field in order]
    actual_known = [field for field in order if field in FIELD_ORDER]
    if actual_known != known_present:
        errors.append(
            "  fields out of order\n"
            f"    expected: {known_present}\n"
            f"    got:      {actual_known}"
        )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="*")
    args = parser.parse_args()
    failed = False

    for filename in args.files:
        path = Path(filename)
        errors = check_file(path)
        if errors:
            print(f"{path}:")
            print("\n".join(errors))
            failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

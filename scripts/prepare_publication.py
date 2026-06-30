#!/usr/bin/env python3
"""Validate or prepare draft posts changed by a publishing pull request."""

from __future__ import annotations

import argparse
import datetime
import re
import subprocess
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

DATE_LINE = re.compile(r"^Date:\s*.*$", re.IGNORECASE)
STATUS_LINE = re.compile(r"^Status:\s*(.*?)\s*$", re.IGNORECASE)


def changed_posts(base_ref: str) -> list[Path]:
    """Return added or modified Markdown posts relative to the PR base."""
    result = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            "--diff-filter=AM",
            "-z",
            f"{base_ref}...HEAD",
            "--",
            "content/posts",
        ],
        check=True,
        capture_output=True,
    )
    return [
        Path(name.decode())
        for name in result.stdout.split(b"\0")
        if name and name.decode().endswith(".md")
    ]


def metadata_lines(lines: list[str]) -> list[str]:
    """Return the metadata header lines, excluding the first blank line."""
    for index, line in enumerate(lines):
        if not line.strip():
            return lines[:index]
    return lines


def draft_status(path: Path) -> bool:
    """Return whether a post metadata header declares draft status."""
    lines = path.read_text(encoding="utf-8").splitlines()
    for line in metadata_lines(lines):
        match = STATUS_LINE.match(line)
        if match:
            status = match.group(1).lower()
            if status != "draft":
                raise ValueError(f"{path}: unsupported Status value {status!r}")
            return True
    return False


def publication_date(now: datetime.datetime | None = None) -> str:
    """Format the publication time in the blog's Taiwan timezone."""
    current = now or datetime.datetime.now(tz=ZoneInfo("Asia/Taipei"))
    return current.astimezone(ZoneInfo("Asia/Taipei")).strftime("%Y-%m-%d %H:%M %z")


def prepare_post(path: Path, date: str) -> bool:
    """Update the publication date and drop any draft status.

    A post may reach this step with ``Status: draft`` already removed on the
    branch; in that case the date is still refreshed to the publication time.
    Returns whether the file content changed.
    """
    original = path.read_text(encoding="utf-8")
    trailing_newline = original.endswith("\n")
    lines = original.splitlines()
    header = metadata_lines(lines)

    status_indexes = [
        index for index, line in enumerate(header) if STATUS_LINE.match(line)
    ]
    if len(status_indexes) > 1:
        raise ValueError(f"{path}: expected at most one Status field")
    if status_indexes:
        status_match = STATUS_LINE.match(header[status_indexes[0]])
        if status_match is None or status_match.group(1).lower() != "draft":
            raise ValueError(f"{path}: expected Status: draft")

    date_indexes = [index for index, line in enumerate(header) if DATE_LINE.match(line)]
    if len(date_indexes) != 1:
        raise ValueError(f"{path}: expected one Date field")

    lines[date_indexes[0]] = f"Date: {date}"
    for index in status_indexes:
        del lines[index]
    updated = "\n".join(lines) + ("\n" if trailing_newline else "")
    path.write_text(updated, encoding="utf-8")
    return updated != original


def check(paths: list[Path]) -> int:
    """Fail when any post changed by a publishing PR is still a draft."""
    drafts = [path for path in paths if draft_status(path)]
    if drafts:
        print("Publishing PR still contains draft posts:", file=sys.stderr)
        for path in drafts:
            print(f"  {path}", file=sys.stderr)
        print(
            "Enable auto-merge to prepare publication metadata.",
            file=sys.stderr,
        )
        return 1
    return 0


def prepare(paths: list[Path], date: str) -> int:
    """Prepare every changed post for publication."""
    changed = [path for path in paths if prepare_post(path, date)]
    if changed:
        print(f"Publication date: {date}")
        for path in changed:
            print(f"Prepared {path}")
    else:
        print("No changed draft posts need preparation.")
    return check(paths)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["check", "prepare"])
    parser.add_argument("--base-ref", required=True)
    parser.add_argument(
        "--date",
        help="publication date override in 'YYYY-MM-DD HH:MM +0800' format",
    )
    args = parser.parse_args()

    posts = changed_posts(args.base_ref)
    if not posts:
        message = "Publishing PR does not change any Markdown posts."
        if args.mode == "prepare":
            # The post may already be on the base branch (e.g. a re-run after an
            # earlier publish); there is nothing to prepare, so succeed quietly
            # instead of failing the auto-merge workflow.
            print(message)
            return 0
        print(message, file=sys.stderr)
        return 1

    try:
        if args.mode == "check":
            return check(posts)
        return prepare(posts, args.date or publication_date())
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

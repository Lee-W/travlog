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
POST_FILENAME = re.compile(r"^(\d+)-.+\.md$")
PUBLISH_COMMIT_PREFIX = "new post:"
PREPARE_COMMIT_PREFIX = "post metadata: prepare publication for #"


def has_publish_commit(base_ref: str) -> bool:
    """Return whether a `new post:` commit exists ahead of the PR base.

    This is the source of truth for "is this a publishing PR" — PR titles are
    freeform and easy to leave stale (e.g. reused from an earlier `new draft:`
    PR), while the commit message follows the repo's enforced commitizen
    convention.
    """
    result = subprocess.run(
        ["git", "log", "--format=%s", f"{base_ref}..HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return any(
        subject.startswith(PUBLISH_COMMIT_PREFIX)
        for subject in result.stdout.splitlines()
    )


def head_is_prepared() -> bool:
    """Return whether publication automation created the branch-tip commit."""
    result = subprocess.run(
        ["git", "log", "-1", "--format=%s"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip().startswith(PREPARE_COMMIT_PREFIX)


def draft_status_text(content: str, label: str | Path) -> bool:
    """Return whether a post's metadata text declares draft status."""
    for line in metadata_lines(content.splitlines()):
        match = STATUS_LINE.match(line)
        if match:
            status = match.group(1).lower()
            if status != "draft":
                raise ValueError(f"{label}: unsupported Status value {status!r}")
            return True
    return False


def base_draft_status(commit: str, path: str) -> bool:
    """Return whether a post was a draft at the PR merge base."""
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        check=True,
        capture_output=True,
        text=True,
    )
    return draft_status_text(result.stdout, path)


def changed_posts(base_ref: str) -> list[Path]:
    """Return posts that this publishing PR intends to publish.

    Added posts always qualify. Modified or renamed posts qualify only when
    either the merge-base version or current version is a draft. This includes
    drafts whose Status field was already removed while excluding collateral
    renames of previously published posts.
    """
    merge_base = subprocess.run(
        ["git", "merge-base", base_ref, "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    result = subprocess.run(
        [
            "git",
            "diff",
            "--name-status",
            "--find-renames",
            "--diff-filter=AMR",
            "-z",
            merge_base,
            "HEAD",
            "--",
            "content/posts",
        ],
        check=True,
        capture_output=True,
    )
    fields = iter(field.decode() for field in result.stdout.split(b"\0") if field)
    posts: list[Path] = []
    for status in fields:
        old_path = next(fields)
        new_path = next(fields) if status.startswith("R") else old_path
        if not new_path.endswith(".md"):
            continue

        path = Path(new_path)
        if status == "A" or draft_status(path):
            posts.append(path)
        elif status == "M" and base_draft_status(merge_base, old_path):
            posts.append(path)
        elif status.startswith("R") and base_draft_status(merge_base, old_path):
            posts.append(path)
    return posts


def metadata_lines(lines: list[str]) -> list[str]:
    """Return the metadata header lines, excluding the first blank line."""
    for index, line in enumerate(lines):
        if not line.strip():
            return lines[:index]
    return lines


def draft_status(path: Path) -> bool:
    """Return whether a post metadata header declares draft status."""
    return draft_status_text(path.read_text(encoding="utf-8"), path)


def filename_number(path: Path) -> int | None:
    """Return a post's numeric filename prefix, if it has one."""
    match = POST_FILENAME.match(path.name)
    return int(match.group(1)) if match else None


def check_filename_numbers(paths: list[Path]) -> int:
    """Require publishing posts to follow the latest published sibling.

    Numbering is scoped to the category/year directory. Draft siblings and all
    posts being published in this run are excluded from the existing sequence.
    Multiple posts published together must occupy the next consecutive numbers.
    """
    publishing_paths = {path.resolve() for path in paths}
    by_directory: dict[Path, list[Path]] = {}
    for path in paths:
        by_directory.setdefault(path.parent, []).append(path)

    errors: list[str] = []
    for directory, publishing_posts in by_directory.items():
        published_numbers = [
            number
            for sibling in directory.glob("*.md")
            if sibling.resolve() not in publishing_paths
            and not draft_status(sibling)
            and (number := filename_number(sibling)) is not None
        ]
        next_number = max(published_numbers, default=0) + 1

        numbered_posts: list[tuple[int, Path]] = []
        for path in publishing_posts:
            number = filename_number(path)
            if number is None:
                errors.append(f"{path}: expected filename to start with a number")
                continue
            numbered_posts.append((number, path))

        for offset, (actual, path) in enumerate(sorted(numbered_posts)):
            expected = next_number + offset
            expected_prefix = f"{expected:02d}-"
            if actual != expected or not path.name.startswith(expected_prefix):
                errors.append(
                    f"{path}: expected filename prefix {expected_prefix} "
                    f"(latest published sibling is {expected - 1:02d})"
                )

    if errors:
        print(
            "Publishing post filenames have incorrect sequence numbers:",
            file=sys.stderr,
        )
        for error in errors:
            print(f"  {error}", file=sys.stderr)
        return 1
    return 0


def corrected_filename(path: Path, number: int) -> Path:
    """Return path with a corrected numeric prefix and the existing suffix."""
    match = POST_FILENAME.match(path.name)
    suffix = path.name.split("-", 1)[1] if match else path.name
    return path.with_name(f"{number:02d}-{suffix}")


def correct_filename_numbers(paths: list[Path]) -> list[Path]:
    """Correct publishing filenames and move colliding drafts after them."""
    publishing_paths = {path.resolve() for path in paths}
    by_directory: dict[Path, list[Path]] = {}
    for path in paths:
        by_directory.setdefault(path.parent, []).append(path)

    replacements: dict[Path, Path] = {}
    for directory, publishing_posts in by_directory.items():
        published_numbers = [
            number
            for sibling in directory.glob("*.md")
            if sibling.resolve() not in publishing_paths
            and not draft_status(sibling)
            and (number := filename_number(sibling)) is not None
        ]
        next_number = max(published_numbers, default=0) + 1
        publishing_posts.sort(
            key=lambda path: (filename_number(path) or sys.maxsize, path.name)
        )
        publishing_destinations = [
            corrected_filename(path, next_number + offset)
            for offset, path in enumerate(publishing_posts)
        ]
        if all(
            source == destination
            for source, destination in zip(publishing_posts, publishing_destinations)
        ):
            continue

        remaining_drafts = sorted(
            (
                sibling
                for sibling in directory.glob("*.md")
                if sibling.resolve() not in publishing_paths and draft_status(sibling)
            ),
            key=lambda path: (filename_number(path) or sys.maxsize, path.name),
        )
        ordered_posts = publishing_posts + remaining_drafts
        for offset, source in enumerate(ordered_posts):
            destination = corrected_filename(source, next_number + offset)
            if source != destination:
                replacements[source] = destination

    temporary_paths: dict[Path, Path] = {}
    for index, source in enumerate(replacements):
        temporary = source.with_name(f".{index}-{source.name}.prepare-publication-tmp")
        if temporary.exists():
            raise ValueError(f"temporary rename path already exists: {temporary}")
        source.rename(temporary)
        temporary_paths[source] = temporary

    for source, destination in replacements.items():
        temporary_paths[source].rename(destination)
        print(f"Renamed {source} -> {destination}")

    return [replacements.get(path, path) for path in paths]


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
    """Validate publication status and filename sequence."""
    failed = check_filename_numbers(paths)
    drafts = [path for path in paths if draft_status(path)]
    if drafts:
        print("Publishing PR still contains draft posts:", file=sys.stderr)
        for path in drafts:
            print(f"  {path}", file=sys.stderr)
        print(
            "Enable auto-merge to prepare publication metadata.",
            file=sys.stderr,
        )
        failed = 1
    return failed


def prepare(paths: list[Path], date: str) -> int:
    """Prepare every changed post for publication."""
    paths = correct_filename_numbers(paths)
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

    try:
        if not has_publish_commit(args.base_ref):
            print(
                f"No {PUBLISH_COMMIT_PREFIX!r} commit ahead of {args.base_ref}; "
                "not a publishing PR."
            )
            return 0

        posts = changed_posts(args.base_ref)
        if not posts:
            message = "Publishing PR does not contain a post to publish."
            print(message, file=sys.stderr)
            return 1

        prepared = head_is_prepared()
        if prepared:
            # Filename correction may renumber other drafts to resolve a path
            # collision. They are part of the automation commit, but they are
            # not posts being published by it.
            posts = [path for path in posts if not draft_status(path)]
            if not posts:
                print(
                    "Prepared branch does not contain a published post.",
                    file=sys.stderr,
                )
                return 1

        if args.mode == "check":
            if not prepared:
                print(
                    "Publishing metadata has not been prepared. "
                    "Enable auto-merge to prepare it.",
                    file=sys.stderr,
                )
                return 1
            return check(posts)
        if prepared:
            print("Publication metadata is already prepared.")
            return check(posts)
        return prepare(posts, args.date or publication_date())
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

"""Backfill `translations.ja.title` into story-ranking YAML from AniList.

`title` holds the Taiwanese Mandarin name, which is what the main site shows.
The Japanese subsite wants the original title, so this fills
`translations.ja.title` from AniList's `title.native` for every entry that
carries an AniList id.

Entries without an AniList id (western films, live-action series, general
novels) are left alone — the templates fall back to `title`.

Editing uses ruamel.yaml round-trip mode to merge translation mappings while
retaining quotes and the comments that mark tier blocks.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import yaml
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import SingleQuotedScalarString

ANILIST_URL = "https://graphql.anilist.co"
USER_AGENT = "entertainment-blog-native-title-backfill/1.0"
RANKING_DIR = Path("content/data/story-ranking")
BATCH_SIZE = 50


def fetch_native_titles(media_ids: list[int]) -> dict[int, str]:
    """Return {anilist_id: native title} for the ids that have one."""
    query = """
    query($ids: [Int]) {
      Page(page: 1, perPage: 50) {
        media(id_in: $ids) {
          id
          title { native romaji }
        }
      }
    }
    """
    titles: dict[int, str] = {}
    for start in range(0, len(media_ids), BATCH_SIZE):
        batch = media_ids[start : start + BATCH_SIZE]
        payload = json.dumps({"query": query, "variables": {"ids": batch}}).encode()
        request = urllib.request.Request(
            ANILIST_URL,
            data=payload,
            headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                result = json.load(response)
        except (urllib.error.URLError, TimeoutError) as error:
            raise RuntimeError(f"failed to query AniList: {error}") from error
        if result.get("errors"):
            raise RuntimeError(f"AniList returned errors: {result['errors']!r}")
        for media in result["data"]["Page"]["media"]:
            native = (media["title"] or {}).get("native")
            if native:
                titles[media["id"]] = normalize(native)
    return titles


def normalize(title: str) -> str:
    """AniList sometimes returns the halfwidth middle dot; the data uses ・."""
    return title.replace("\uff65", "\u30fb")


def native_title(entry: dict[str, Any]) -> str | None:
    return (entry.get("translations") or {}).get("ja", {}).get("title")


def first_anilist_id(entry: dict[str, Any]) -> int | None:
    ids = (entry.get("external_ids") or {}).get("anilist") or []
    return ids[0] if ids else None


def plan_for_file(
    path: Path, native_by_id: dict[int, str]
) -> list[tuple[int, str, str]]:
    """Return [(entry index, title, native)] for entries needing a backfill."""
    entries = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    plan = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict) or native_title(entry) is not None:
            continue
        anilist_id = first_anilist_id(entry)
        native = native_by_id.get(anilist_id) if anilist_id else None
        if native and native != entry.get("title"):
            plan.append((index, entry.get("title", ""), native))
    return plan


def apply_to_file(path: Path, plan: list[tuple[int, str, str]]) -> int:
    """Merge missing Japanese titles, retaining other translations and comments."""
    by_index = {index: native for index, _, native in plan}
    document = YAML()
    document.preserve_quotes = True
    document.width = 1000
    entries = document.load(path.read_text(encoding="utf-8"))
    written = 0
    for index, native in by_index.items():
        entry = entries[index]
        if native_title(entry) is not None:
            continue
        translations = entry.setdefault("translations", {})
        translations.setdefault("ja", {})["title"] = SingleQuotedScalarString(native)
        written += 1
    if written:
        with path.open("w", encoding="utf-8") as output:
            document.dump(entries, output)
    return written


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="write the changes; without it the script only reports them",
    )
    parser.add_argument("--limit", type=int, default=15, help="rows to show per file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    files = sorted(RANKING_DIR.glob("*.yaml"))
    if not files:
        print(f"no YAML under {RANKING_DIR}", file=sys.stderr)
        return 1

    wanted: set[int] = set()
    for path in files:
        for entry in yaml.safe_load(path.read_text(encoding="utf-8")) or []:
            if isinstance(entry, dict) and native_title(entry) is None:
                anilist_id = first_anilist_id(entry)
                if anilist_id:
                    wanted.add(anilist_id)

    print(f"entries with an AniList id and no Japanese title: {len(wanted)}")
    native_by_id = fetch_native_titles(sorted(wanted)) if wanted else {}
    print(f"AniList returned a native title for {len(native_by_id)} of them\n")

    total = 0
    for path in files:
        plan = plan_for_file(path, native_by_id)
        total += len(plan)
        entries = yaml.safe_load(path.read_text(encoding="utf-8")) or []
        print(f"{path.name}: {len(plan)} of {len(entries)} entries")
        for _, title, native in plan[: args.limit]:
            print(f"    {title}  ->  {native}")
        if len(plan) > args.limit:
            print(f"    ... {len(plan) - args.limit} more")
        if args.apply and plan:
            apply_to_file(path, plan)

    print(
        f"\n{'wrote' if args.apply else 'would write'} translations.ja.title for {total} entries"
    )
    if not args.apply:
        print("re-run with --apply to write them")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

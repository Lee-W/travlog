#!/usr/bin/env python3
"""Verify bidirectional consistency between story-ranking and AniList."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ANILIST_URL = "https://graphql.anilist.co"
RANKING_MEDIA_TYPES = {
    "anime.yaml": "ANIME",
    "manga-completed.yaml": "MANGA",
    "manga-ongoing.yaml": "MANGA",
    "novel.yaml": "MANGA",
}
TIER_SCORES = {
    "SSS": 10,
    "SS": 9,
    "S": 8,
    "A": 7,
    "B": 6,
    "C": 5,
    "D": 4,
    "E": 3,
    "F": 2,
    "G": 1,
}


@dataclass(frozen=True)
class RankingEntry:
    filename: str
    title: str
    tier: str | None
    media_type: str | None
    anilist_ids: tuple[int, ...]
    anilist_scores: tuple[tuple[int, int], ...] = ()

    @property
    def label(self) -> str:
        suffix = f" ({self.tier})" if self.tier else ""
        return f"{self.filename}: {self.title!r}{suffix}"


def load_ranking_entries(yaml_dir: Path) -> tuple[list[RankingEntry], list[str]]:
    entries: list[RankingEntry] = []
    errors: list[str] = []

    paths = sorted(yaml_dir.glob("*.yaml"))
    pending_path = yaml_dir.parent / "anilist-pending.yaml"
    if pending_path.exists():
        paths.append(pending_path)
    for path in paths:
        filename = path.name
        media_type = RANKING_MEDIA_TYPES.get(filename)
        rows = yaml.safe_load(path.read_text(encoding="utf-8")) or []
        for index, row in enumerate(rows, start=1):
            title = row.get("title", "")
            tier = row.get("tier")
            label = f"{filename} entry {index}: {title!r}"
            if media_type and tier not in TIER_SCORES:
                errors.append(f"{label} has invalid tier {tier!r}")
                continue

            external_ids = row.get("external_ids") or {}
            raw_ids = external_ids.get("anilist") if external_ids else None
            if raw_ids is None:
                ids: tuple[int, ...] = ()
            elif not isinstance(raw_ids, list) or not raw_ids:
                errors.append(f"{label} has invalid AniList IDs: {raw_ids!r}")
                ids = ()
            elif not all(isinstance(item, int) and item > 0 for item in raw_ids):
                errors.append(f"{label} has invalid AniList IDs: {raw_ids!r}")
                ids = ()
            else:
                ids = tuple(raw_ids)

            external_scores = row.get("external_scores") or {}
            raw_scores = external_scores.get("anilist", {})
            if not isinstance(raw_scores, dict) or not all(
                isinstance(media_id, int)
                and media_id in ids
                and isinstance(score, int)
                and 1 <= score <= 10
                for media_id, score in raw_scores.items()
            ):
                errors.append(
                    f"{label} has invalid external_scores.anilist: {raw_scores!r}"
                )
                scores: tuple[tuple[int, int], ...] = ()
            else:
                scores = tuple(raw_scores.items())

            if media_type or ids:
                entries.append(
                    RankingEntry(filename, title, tier, media_type, ids, scores)
                )

    return entries, errors


def fetch_anilist_collection(user: str, media_type: str) -> dict[int, dict[str, Any]]:
    query = """
    query($user: String!, $type: MediaType!) {
      MediaListCollection(userName: $user, type: $type) {
        lists {
          entries {
            status
            score
            media {
              id
              type
              format
              title { romaji english native }
            }
          }
        }
      }
    }
    """
    payload = json.dumps(
        {"query": query, "variables": {"user": user, "type": media_type}}
    ).encode()
    request = urllib.request.Request(
        ANILIST_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "entertainment-blog-story-ranking-check/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.load(response)
    except (urllib.error.URLError, TimeoutError) as error:
        raise RuntimeError(f"failed to query AniList: {error}") from error

    if result.get("errors"):
        raise RuntimeError(f"AniList returned errors: {result['errors']!r}")

    collection = result["data"]["MediaListCollection"]
    if collection is None:
        raise RuntimeError(f"AniList user {user!r} was not found")

    entries: dict[int, dict[str, Any]] = {}
    for media_list in collection["lists"]:
        for entry in media_list["entries"]:
            entries[entry["media"]["id"]] = entry
    return entries


def load_fixture(path: Path) -> dict[str, dict[int, dict[str, Any]]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {
        media_type: {entry["media"]["id"]: entry for entry in rows}
        for media_type, rows in raw.items()
    }


def media_title(entry: dict[str, Any]) -> str:
    title = entry["media"]["title"]
    return title.get("english") or title.get("romaji") or title.get("native") or ""


def validate(
    ranking_entries: list[RankingEntry],
    collections: dict[str, dict[int, dict[str, Any]]],
) -> list[str]:
    errors: list[str] = []
    owners: dict[tuple[str, int], list[RankingEntry]] = {}

    for ranking in ranking_entries:
        score_overrides = dict(ranking.anilist_scores)
        for media_id in ranking.anilist_ids:
            if ranking.media_type:
                candidate_types = [ranking.media_type]
            else:
                candidate_types = [
                    media_type
                    for media_type, collection in collections.items()
                    if media_id in collection
                ]
            if len(candidate_types) != 1:
                errors.append(
                    f"{ranking.label} maps AniList {media_id}, but its media type "
                    "cannot be determined from the user's lists"
                )
                continue

            media_type = candidate_types[0]
            collection = collections[media_type]
            key = (media_type, media_id)
            previous = owners.get(key, [])
            if previous and any(
                owner.filename == "anilist-pending.yaml" for owner in previous
            ) != (ranking.filename == "anilist-pending.yaml"):
                errors.append(
                    f"AniList {media_type} {media_id} is both pending and ranked: "
                    f"{previous[0].label} and {ranking.label}"
                )
                continue
            owners.setdefault(key, []).append(ranking)

            entry = collection.get(media_id)
            if entry is None:
                errors.append(
                    f"{ranking.label} maps AniList {media_id}, "
                    "but it is absent from the user's list"
                )
                continue

            expected_score = score_overrides.get(media_id)
            if expected_score is None and ranking.tier:
                expected_score = TIER_SCORES[ranking.tier]
            actual_score = entry["score"]
            if expected_score is not None and actual_score != expected_score:
                errors.append(
                    f"{ranking.label} expects score {expected_score}, "
                    f"but AniList {media_id} {media_title(entry)!r} is {actual_score}"
                )

            media_format = entry["media"]["format"]
            if ranking.filename == "novel.yaml" and media_format != "NOVEL":
                errors.append(
                    f"{ranking.label} maps AniList {media_id} with format "
                    f"{media_format}, expected NOVEL"
                )
            if ranking.filename.startswith("manga-") and media_format == "NOVEL":
                errors.append(
                    f"{ranking.label} maps AniList {media_id} with format NOVEL"
                )

    for media_type, collection in collections.items():
        for media_id, entry in collection.items():
            if entry["score"] <= 0:
                continue
            if media_type == "ANIME" and entry["status"] != "COMPLETED":
                continue
            if (media_type, media_id) not in owners:
                errors.append(
                    f"AniList {media_type} {media_id} {media_title(entry)!r} "
                    f"has score {entry['score']} but no story-ranking mapping"
                )

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check bidirectional AniList/story-ranking consistency"
    )
    parser.add_argument("--user", default="clleew", help="AniList username")
    parser.add_argument(
        "--fixture",
        type=Path,
        help="Read ANIME/MANGA collection data from JSON instead of the network",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).parent.parent
    yaml_dir = repo_root / "content" / "data" / "story-ranking"
    ranking_entries, errors = load_ranking_entries(yaml_dir)

    if args.fixture:
        collections = load_fixture(args.fixture)
    else:
        try:
            collections = {
                media_type: fetch_anilist_collection(args.user, media_type)
                for media_type in ("ANIME", "MANGA")
            }
        except RuntimeError as error:
            print(error, file=sys.stderr)
            return 2

    errors.extend(validate(ranking_entries, collections))
    if errors:
        print("AniList/story-ranking drift found:", file=sys.stderr)
        for error in errors:
            print(f"  {error}", file=sys.stderr)
        return 1

    mapped = sum(len(entry.anilist_ids) for entry in ranking_entries)
    print(
        f"AniList/story-ranking: {len(ranking_entries)} ranking entries, "
        f"{mapped} AniList media verified OK"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

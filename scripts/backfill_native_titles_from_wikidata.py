"""Backfill `translations.ja.title` for films and documentaries via Wikidata.

Anime and manga get their original title from AniList
(`backfill_story_ranking_native_titles.py`). Western films, documentaries and
live-action Star Wars entries have no AniList id but do carry a Letterboxd
slug, which Wikidata indexes as P6127.

Two candidates come back per film. The Japanese Wikipedia article title is
preferred because it is normally the Japanese release title; the Wikidata `ja`
label is the fallback. They usually agree, and where they do not the label is
often a non-standard transliteration — "Everything Everywhere All at Once" is
エブリシング・エブリホウェアー… as a label but エブリシング・エブリウェア… as an
article, and the latter is the title the film was released under.

Entries with neither an AniList id nor a Letterboxd slug are left alone; the
templates fall back to `title`.
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import yaml
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import SingleQuotedScalarString

SPARQL_URL = "https://query.wikidata.org/sparql"
USER_AGENT = "entertainment-blog-native-title-backfill/1.0 (hello+travlog@wei-lee.me)"
RANKING_DIR = Path("content/data/story-ranking")
BATCH_SIZE = 40

QUERY = """
SELECT ?slug ?label ?article WHERE {
  VALUES ?slug { %s }
  ?item wdt:P6127 ?slug .
  OPTIONAL { ?item rdfs:label ?label . FILTER(lang(?label) = "ja") }
  OPTIONAL {
    ?article schema:about ?item ; schema:isPartOf <https://ja.wikipedia.org/> .
  }
}
"""


def article_title(url: str) -> str:
    # Split on /wiki/, not the last slash: Japanese article titles contain
    # slashes themselves ("ローグ・ワン/スター・ウォーズ・ストーリー").
    return urllib.parse.unquote(url.split("/wiki/", 1)[-1]).replace("_", " ")


def fetch_japanese_titles(slugs: list[str]) -> dict[str, str]:
    """Return {letterboxd slug: Japanese title} for the slugs Wikidata knows."""
    titles: dict[str, str] = {}
    for start in range(0, len(slugs), BATCH_SIZE):
        batch = slugs[start : start + BATCH_SIZE]
        values = " ".join(f'"{slug}"' for slug in batch)
        url = f"{SPARQL_URL}?format=json&query=" + urllib.parse.quote(QUERY % values)
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/sparql-results+json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                result = json.load(response)
        except (urllib.error.URLError, TimeoutError) as error:
            raise RuntimeError(f"failed to query Wikidata: {error}") from error
        for binding in result["results"]["bindings"]:
            slug = binding["slug"]["value"]
            article = binding.get("article", {}).get("value")
            label = binding.get("label", {}).get("value")
            title = article_title(article) if article else label
            if title:
                titles[slug] = title
        if start + BATCH_SIZE < len(slugs):
            time.sleep(1)
    return titles


def native_title(entry: dict[str, Any]) -> str | None:
    return (entry.get("translations") or {}).get("ja", {}).get("title")


def first_letterboxd_slug(entry: dict[str, Any]) -> str | None:
    slugs = (entry.get("external_ids") or {}).get("letterboxd") or []
    return slugs[0] if slugs else None


def apply_to_file(path: Path, by_index: dict[int, str]) -> None:
    """Merge missing Japanese titles, retaining other translations and comments."""
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="write the changes")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    files = sorted(RANKING_DIR.glob("*.yaml"))
    wanted: list[str] = []
    for path in files:
        for entry in yaml.safe_load(path.read_text(encoding="utf-8")) or []:
            if isinstance(entry, dict) and native_title(entry) is None:
                slug = first_letterboxd_slug(entry)
                if slug and slug not in wanted:
                    wanted.append(slug)

    print(f"entries with a Letterboxd slug and no Japanese title: {len(wanted)}")
    titles = fetch_japanese_titles(wanted) if wanted else {}
    print(f"Wikidata knows a Japanese title for {len(titles)} of them\n")

    total = missing = 0
    for path in files:
        entries = yaml.safe_load(path.read_text(encoding="utf-8")) or []
        by_index: dict[int, str] = {}
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict) or native_title(entry) is not None:
                continue
            slug = first_letterboxd_slug(entry)
            japanese = titles.get(slug) if slug else None
            if slug and not japanese:
                missing += 1
                print(
                    f"    no Japanese title: {path.name}: {entry.get('title')} ({slug})"
                )
            if japanese and japanese != entry.get("title"):
                by_index[index] = japanese
        if by_index:
            print(f"{path.name}: {len(by_index)} entries")
            for index, japanese in list(by_index.items())[:5]:
                print(f"    {entries[index].get('title')}  ->  {japanese}")
            if len(by_index) > 5:
                print(f"    ... {len(by_index) - 5} more")
            if args.apply:
                apply_to_file(path, by_index)
        total += len(by_index)

    print(
        f"\n{'wrote' if args.apply else 'would write'} translations.ja.title for {total} entries"
    )
    print(f"{missing} entries had a slug Wikidata does not know")
    if not args.apply:
        print("re-run with --apply to write them")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

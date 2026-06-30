#!/usr/bin/env python3
"""Verify story-ranking YAML anchors point to correct headings in review posts.

Checks:
1. Referenced post file exists
2. Anchor exists in the post
3. Heading at that anchor semantically matches the work title / review text
4. A direct review article links back to its seasonal roundup
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import markdown
import yaml
from markdown.extensions.toc import TocExtension


def get_anchor_map(filepath: Path) -> dict[str, str]:
    """Return {anchor_id: heading_name} for all TOC headings in a post."""
    content = filepath.read_text(encoding="utf-8")
    md = markdown.Markdown(extensions=[TocExtension()])
    md.convert(content)
    result: dict[str, str] = {}

    def walk(tokens: list) -> None:
        for tok in tokens:
            result[tok["id"]] = tok["name"]
            walk(tok.get("children", []))

    walk(md.toc_tokens)
    return result


def keywords(s: str) -> set[str]:
    """CJK bigrams + ASCII words (>=3 chars) for semantic matching."""
    cjk = [
        s[i : i + 2]
        for i in range(len(s) - 1)
        if all("一" <= c <= "鿿" for c in s[i : i + 2])
    ]
    ascii_words = re.findall(r"[A-Za-z0-9]{3,}", s)
    return set(cjk + [w.lower() for w in ascii_words])


def review_items(entry: dict) -> list[dict]:
    """Normalize the legacy single-review mapping and the usual review list."""
    reviews = entry.get("reviews") or []
    if isinstance(reviews, dict):
        return [reviews]
    return reviews


def filename_post_path(href: str, repo_root: Path) -> Path | None:
    """Resolve a content-local review href without requiring an anchor."""
    match = re.match(r"\{filename\}(/posts/review/[^#]+\.md)(?:#.*)?$", href)
    if not match:
        return None
    return repo_root / "content" / match.group(1).lstrip("/")


def check_yaml_file(
    yaml_path: Path, repo_root: Path, anchor_cache: dict[Path, dict[str, str]]
) -> list[str]:
    errors: list[str] = []
    raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or []

    for entry in raw:
        title: str = entry.get("title", "")
        for rev in review_items(entry):
            href = rev.get("href", "")
            season_href = rev.get("season_href", "")

            direct_path = filename_post_path(href, repo_root)
            if direct_path and not direct_path.exists():
                errors.append(
                    f"  {yaml_path.name}: {title!r} — missing file "
                    f"{direct_path.relative_to(repo_root)}"
                )

            anchor_href = season_href or href
            m = re.match(r"\{filename\}(/posts/review/\S+?)#(\S+)", anchor_href)
            if not m:
                continue
            relpath, anchor = m.group(1), m.group(2)
            post_path = repo_root / "content" / relpath.lstrip("/")

            if not post_path.exists():
                errors.append(
                    f"  {yaml_path.name}: {title!r} — missing file {post_path.relative_to(repo_root)}"
                )
                continue

            if post_path not in anchor_cache:
                anchor_cache[post_path] = get_anchor_map(post_path)

            amap = anchor_cache[post_path]
            if anchor not in amap:
                errors.append(
                    f"  {yaml_path.name}: {title!r} ({rev.get('text', '')!r})"
                    f" — anchor #{anchor} not found in {post_path.name}"
                )
                continue

            heading = amap[anchor]
            combined_kw = keywords(title) | keywords(rev.get("text", ""))
            if combined_kw and not (combined_kw & keywords(heading)):
                errors.append(
                    f"  {yaml_path.name}: {title!r} ({rev.get('text', '')!r})"
                    f"\n    href #{anchor} → heading {heading!r}  ← semantic mismatch"
                )

            if season_href and direct_path and direct_path.exists():
                direct_content = direct_path.read_text(encoding="utf-8")
                if season_href not in direct_content:
                    errors.append(
                        f"  {yaml_path.name}: {title!r} — {direct_path.name} lacks "
                        f"seasonal backlink to {season_href}"
                    )

    return errors


def check_page_references(yaml_dir: Path, page_path: Path) -> list[str]:
    """Cross-check that every YAML in the directory is surfaced on the page,
    and that every YAML the page references actually exists.

    Catches orphan YAML files (data exists but never rendered) and dangling
    references (page points at a missing file).
    """
    errors: list[str] = []
    if not page_path.exists():
        return [f"  page not found: {page_path.name}"]

    page_text = page_path.read_text(encoding="utf-8")
    referenced = {
        Path(m).name
        for m in re.findall(r"data/story-ranking/([A-Za-z0-9_-]+\.yaml)", page_text)
    }
    on_disk = {p.name for p in yaml_dir.glob("*.yaml")}

    for name in sorted(on_disk - referenced):
        errors.append(
            f"  orphan YAML: {name} exists but is not referenced in {page_path.name}"
        )
    for name in sorted(referenced - on_disk):
        errors.append(
            f"  dangling reference: {page_path.name} references {name} but the file is missing"
        )
    return errors


def main() -> int:
    repo_root = Path(__file__).parent.parent
    yaml_dir = repo_root / "content" / "data" / "story-ranking"
    page_path = repo_root / "content" / "pages" / "story-ranking.md"
    anchor_cache: dict[Path, dict[str, str]] = {}
    all_errors: list[str] = []
    total_hrefs = 0

    for yaml_path in sorted(yaml_dir.glob("*.yaml")):
        errors = check_yaml_file(yaml_path, repo_root, anchor_cache)
        all_errors.extend(errors)
        raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or []
        total_hrefs += sum(
            sum(1 + bool(review.get("season_href")) for review in review_items(entry))
            for entry in raw
        )

    all_errors.extend(check_page_references(yaml_dir, page_path))

    if all_errors:
        print("story-ranking errors found:", file=sys.stderr)
        for e in all_errors:
            print(e, file=sys.stderr)
        return 1

    print(f"story-ranking: {total_hrefs} hrefs verified OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

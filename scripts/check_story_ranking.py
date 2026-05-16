#!/usr/bin/env python3
"""Verify story-ranking YAML anchors point to correct headings in review posts.

Checks:
1. Referenced post file exists
2. Anchor exists in the post
3. Heading at that anchor semantically matches the work title / review text
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


def check_yaml_file(
    yaml_path: Path, repo_root: Path, anchor_cache: dict[Path, dict[str, str]]
) -> list[str]:
    errors: list[str] = []
    raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or []

    for entry in raw:
        title: str = entry.get("title", "")
        for rev in entry.get("reviews", []):
            href: str = rev.get("href", "")
            m = re.match(r"\{filename\}(/posts/review/\S+?)#(\S+)", href)
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

    return errors


def main() -> int:
    repo_root = Path(__file__).parent.parent
    yaml_dir = repo_root / "content" / "data" / "story-ranking"
    anchor_cache: dict[Path, dict[str, str]] = {}
    all_errors: list[str] = []
    total_hrefs = 0

    for yaml_path in sorted(yaml_dir.glob("*.yaml")):
        errors = check_yaml_file(yaml_path, repo_root, anchor_cache)
        all_errors.extend(errors)
        raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or []
        total_hrefs += sum(len(e.get("reviews", [])) for e in raw)

    if all_errors:
        print("story-ranking anchor errors found:", file=sys.stderr)
        for e in all_errors:
            print(e, file=sys.stderr)
        return 1

    print(f"story-ranking: {total_hrefs} hrefs verified OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

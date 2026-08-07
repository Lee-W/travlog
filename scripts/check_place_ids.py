"""Verify place id/name uniqueness across content/places/.

`venue_ref` in content/data/*.yaml resolves against a *global* index that
pelican-tabular builds from every readable YAML under content/places/. The
lookup is `by_id.get(ref) or by_name.get(ref)` — ids are consulted first, then
names. pelican-osm keys a marker's photos by `props.id || props.name`
(see osm-map.js). Both mechanisms make the id/name namespace load-bearing, and
both fail in ways that are easy to miss:

Checks:
1. Duplicate id — a `venue_ref` pointing at it raises "ambiguous" and fails the
   build, but only once something actually references it. Until then: silent.
2. Same name across records where any of them lacks an id — the name is then a
   live ref key resolving to several records, *and* (when those records land on
   one map) their photos collide in the shared images map, the later file
   silently overwriting the earlier one's list. Distinct ids fix both.
3. An id equal to some *other* record's name — the worst case: `by_id` wins, so
   the ref silently resolves to the id holder with no error at all.

Duplicate names are allowed on purpose: one place can be a pilgrimage site for
two works, or both a pilgrimage site and a restaurant. Those are separate
records by necessity (pelican-osm has no cross-file place ref, and the map
layer field is compared with `===`, so one record can only sit in one layer).
This script only insists each of them carries its own id.
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

import yaml

PLACES_DIR = Path("content/places")


def load_records(path: Path) -> list[dict]:
    """Return the place records in `path`, mirroring how the plugins read it.

    Returns [] for shapes the plugins skip rather than raising: schema files,
    and the dict-of-id files under theaters/ (pelican-tabular logs
    "skipping unreadable ... got dict" for those and leaves them out of the ref
    index entirely, so they cannot collide with anything).
    """
    if path.name.startswith("_"):
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("locations"), list):
        items = data["locations"]
    elif isinstance(data, list):
        items = data
    else:
        return []
    return [it for it in items if isinstance(it, dict)]


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    places = repo_root / PLACES_DIR
    if not places.is_dir():
        print(f"place-ids: {PLACES_DIR} not found", file=sys.stderr)
        return 1

    by_id: dict[str, list[str]] = defaultdict(list)
    by_name: dict[str, list[tuple[str, str | None]]] = defaultdict(list)
    total = 0

    for path in sorted(places.rglob("*.yaml")):
        rel = path.relative_to(repo_root).as_posix()
        for record in load_records(path):
            total += 1
            place_id = record.get("id")
            name = record.get("name")
            if place_id not in (None, ""):
                by_id[str(place_id)].append(rel)
            if name not in (None, ""):
                by_name[str(name)].append(
                    (rel, str(place_id) if place_id not in (None, "") else None)
                )

    errors: list[str] = []

    for place_id, paths in sorted(by_id.items()):
        if len(paths) > 1:
            where = ", ".join(sorted(set(paths)))
            errors.append(
                f"duplicate id {place_id!r} in {where}\n"
                f"    a venue_ref to it fails the build as ambiguous; "
                f"give each record its own id"
            )

    for name, holders in sorted(by_name.items()):
        if len(holders) < 2:
            continue
        missing = [rel for rel, place_id in holders if place_id is None]
        if missing:
            where = ", ".join(sorted({rel for rel, _ in holders}))
            errors.append(
                f"name {name!r} is used by {len(holders)} records ({where}) "
                f"but {len(missing)} of them have no id\n"
                f"    without an id the name becomes the photo key, so records "
                f"on the same map overwrite each other's images; "
                f"give each record its own id"
            )

    for place_id in sorted(by_id):
        if place_id in by_name:
            holders = {rel for rel, _ in by_name[place_id]}
            errors.append(
                f"id {place_id!r} is also another record's name "
                f"(in {', '.join(sorted(holders))})\n"
                f"    ids are matched before names, so a ref to it resolves to "
                f"the id holder silently; rename one of them"
            )

    if errors:
        print("place id/name errors found:", file=sys.stderr)
        for error in errors:
            print(f"  {error}", file=sys.stderr)
        return 1

    dup_names = sum(1 for holders in by_name.values() if len(holders) > 1)
    print(
        f"place-ids: {total} records, {len(by_id)} ids OK "
        f"({dup_names} intentional same-name groups, all with distinct ids)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pillow-heif>=0.18",
#   "questionary>=2.0.1",
#   "ruamel.yaml>=0.18",
# ]
# ///
"""Manage pilgrimage image references in YAML location files.

Commands:
  check   — show images in directories not referenced in YAML
  add     — add a single image to its YAML (photo must already be in images dir)
  batch   — add all unreferenced images; use -i for interactive GPS fallback
  process — interactive wizard: accepts dirs and/or explicit files (from anywhere)
"""

from __future__ import annotations

import argparse
import json
import math
import re as _re
import shutil
import subprocess
import sys
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq

REPO_ROOT = Path(__file__).parent.parent
IMAGES_DIR = REPO_ROOT / "content" / "images" / "pilgrimage"
PLACES_DIR = REPO_ROOT / "content" / "places" / "pilgrimage"
IMAGE_SUFFIXES = {
    ".jpg",
    ".jpeg",
    ".png",
    ".JPG",
    ".JPEG",
    ".PNG",
    ".heic",
    ".HEIC",
    ".webp",
}
GPS_MATCH_THRESHOLD_KM = 1.0

_tty = sys.stdout.isatty()
GREEN = "\033[32m" if _tty else ""
YELLOW = "\033[33m" if _tty else ""
RED = "\033[31m" if _tty else ""
BOLD = "\033[1m" if _tty else ""
DIM = "\033[2m" if _tty else ""
RESET = "\033[0m" if _tty else ""


# ── core helpers ──────────────────────────────────────────────────────────────


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return r * 2 * math.asin(math.sqrt(a))


def get_exif(image_path: Path) -> dict:
    result = subprocess.run(
        [
            "exiftool",
            "-json",
            "-n",
            "-GPSLatitude",
            "-GPSLongitude",
            "-DateTimeOriginal",
            str(image_path),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return {}
    data = json.loads(result.stdout)
    return data[0] if data else {}


def yaml_image_path(image_path: Path) -> str:
    rel = image_path.relative_to(REPO_ROOT / "content")
    return "/" + str(rel)


def all_yaml_files() -> list[Path]:
    return sorted(
        p
        for p in PLACES_DIR.iterdir()
        if p.suffix == ".yaml" and not p.name.startswith("_")
    )


def find_yaml_for_dir(dirname: str) -> Path | None:
    candidate = PLACES_DIR / f"{dirname}.yaml"
    return candidate if candidate.exists() else None


def load_yaml(path: Path) -> tuple[YAML, dict]:
    yml = YAML()
    yml.preserve_quotes = True
    yml.width = 4096
    data = yml.load(path) or {}
    return yml, data


def save_yaml(yml: YAML, data: dict, path: Path) -> None:
    yml.dump(data, path)


def all_referenced_images(data: dict) -> set[str]:
    refs: set[str] = set()
    for loc in data.get("locations") or []:
        for img in loc.get("images") or []:
            refs.add(img)
    return refs


def best_location_match(data: dict, lat: float, lon: float) -> tuple[int | None, float]:
    """Return (index, distance_km) of closest location, or (None, inf)."""
    best_idx, best_dist = None, float("inf")
    for i, loc in enumerate(data.get("locations") or []):
        if loc.get("lat") is None or loc.get("lon") is None:
            continue
        dist = haversine_km(lat, lon, loc["lat"], loc["lon"])
        if dist < best_dist:
            best_dist = dist
            best_idx = i
    return best_idx, best_dist


# ── interactive prompts ───────────────────────────────────────────────────────


def _prompt_choice(
    prompt: str, lo: int, hi: int, extra: dict[str, str] | None = None
) -> int | str | None:
    """Prompt for int in [lo, hi] or any key in extra. Returns None on skip/interrupt."""
    extras = extra or {}
    while True:
        try:
            raw = input(prompt).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return None
        if not raw:
            return None
        if raw in extras:
            return raw
        try:
            n = int(raw)
            if lo <= n <= hi:
                return n
            print(f"  請輸入 {lo}–{hi}" + (f" 或 {'/'.join(extras)}" if extras else ""))
        except ValueError:
            print("  請輸入數字" + (f" 或 {'/'.join(extras)}" if extras else ""))


def _prompt_new_location(
    data: dict, lat: float | None, lon: float | None, date_str: str | None
) -> dict:
    """Interactively prompt for name/city, append a new location to data, and return it."""
    print()
    try:
        name = input("  地點名稱：").strip() or "TODO"
        city = input("  縣市：").strip() or "TODO"
        country = input("  國家 [日本]：").strip() or "日本"
    except EOFError, KeyboardInterrupt:
        print()
        name, city, country = "TODO", "TODO", "日本"

    loc: CommentedMap = CommentedMap()
    loc["name"] = name
    loc["lat"] = round(lat, 6) if lat is not None else 0.0
    loc["lon"] = round(lon, 6) if lon is not None else 0.0
    loc["notes"] = ""
    if date_str:
        loc["date"] = date_str
    loc["country"] = country
    loc["city"] = city
    loc["tags"] = CommentedSeq()
    loc["images"] = CommentedSeq()
    data["locations"].append(loc)
    return loc


def pick_location_interactive(
    data: dict,
    lat: float | None,
    lon: float | None,
    image_name: str,
    date_str: str | None = None,
) -> dict | None:
    """Interactively pick a location from data['locations']. Returns the loc dict or None to skip."""
    locations = data.get("locations") or []

    if not locations:
        print(f"  {YELLOW}此系列尚無任何地點，直接新增{RESET}")
        return _prompt_new_location(data, lat, lon, date_str)

    # Sort by distance if GPS available
    if lat is not None and lon is not None:
        order = sorted(
            range(len(locations)),
            key=lambda i: (
                haversine_km(lat, lon, locations[i]["lat"], locations[i]["lon"])
                if locations[i].get("lat") is not None
                else float("inf")
            ),
        )
    else:
        order = list(range(len(locations)))

    print("  選擇地點：")
    for display_n, real_i in enumerate(order, start=1):
        loc = locations[real_i]
        dist_str = ""
        if lat is not None and lon is not None and loc.get("lat") is not None:
            dist = haversine_km(lat, lon, loc["lat"], loc["lon"])
            tag = f" {GREEN}←{RESET}" if dist <= GPS_MATCH_THRESHOLD_KM else ""
            dist_str = f"  {DIM}({dist:.1f} km){RESET}{tag}"
        print(f"  [{display_n}] {loc.get('name', '?')}{dist_str}")
    print("  [n] 新增地點")
    print("  [0] 跳過此照片")

    choice = _prompt_choice(
        f"  選擇 [0–{len(locations)}/n]: ", 0, len(locations), extra={"n": "新增"}
    )
    if choice is None or choice == 0:
        return None
    if choice == "n":
        return _prompt_new_location(data, lat, lon, date_str)
    return locations[order[int(choice) - 1]]


def pick_anime_interactive(
    image_name: str, lat: float | None, lon: float | None
) -> tuple[Path, YAML, dict] | tuple[None, None, None]:
    """Interactively pick which anime series. Returns (yaml_path, yml, data) or (None, None, None)."""
    all_files = all_yaml_files()

    # Load all + compute GPS distance
    entries: list[tuple[float, Path, YAML, dict]] = []
    for p in all_files:
        yml, data = load_yaml(p)
        if lat is not None and lon is not None:
            _, dist = best_location_match(data, lat, lon)
        else:
            dist = float("inf")
        entries.append((dist, p, yml, data))

    entries.sort(key=lambda x: x[0])

    print(f"\n{BOLD}📷 {image_name}{RESET}")

    # Auto-accept clear GPS match
    if lat is not None and lon is not None and entries[0][0] <= GPS_MATCH_THRESHOLD_KM:
        dist, yaml_path, yml, data = entries[0]
        best_idx, _ = best_location_match(data, lat, lon)
        loc_name = data["locations"][best_idx]["name"] if best_idx is not None else "?"
        print(
            f"  GPS 自動匹配：{BOLD}{data.get('work')}{RESET} → {loc_name}  {DIM}({dist:.1f} km){RESET}"
        )
        try:
            confirm = input("  [Enter 確認 / n 手動選擇] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return None, None, None
        if confirm not in ("n", "no"):
            return yaml_path, yml, data

    # Show GPS-ranked shortlist (up to 6) or full list
    gps_ranked = [e for e in entries if e[0] < float("inf")][:6]

    def _show_full_list() -> tuple[Path, YAML, dict] | tuple[None, None, None]:
        print("\n  所有系列：")
        for i, (_, p, _, d) in enumerate(entries, start=1):
            print(f"  [{i:2}] {d.get('work', p.stem)}")
        print("  [ 0] 跳過")
        choice = _prompt_choice(f"  選擇 [0–{len(entries)}]: ", 0, len(entries))
        if choice is None or choice == 0:
            return None, None, None
        _, yaml_path, yml, data = entries[int(choice) - 1]
        return yaml_path, yml, data

    if gps_ranked and lat is not None:
        print("  GPS 鄰近系列：")
        for i, (dist, p, _, d) in enumerate(gps_ranked, start=1):
            print(f"  [{i}] {d.get('work', p.stem)}  {DIM}({dist:.1f} km){RESET}")
        print("  [m] 顯示全部系列")
        print("  [0] 跳過")
        choice = _prompt_choice(
            f"  選擇 [0–{len(gps_ranked)}/m]: ", 0, len(gps_ranked), extra={"m": "全部"}
        )
        if choice is None or choice == 0:
            return None, None, None
        if choice == "m":
            return _show_full_list()
        _, yaml_path, yml, data = gps_ranked[int(choice) - 1]
        return yaml_path, yml, data

    return _show_full_list()


# ── check ─────────────────────────────────────────────────────────────────────


def cmd_check(no_images: bool = False) -> int:
    issues: list[str] = []

    if no_images:
        # Report YAML locations that have no images
        for yaml_path in all_yaml_files():
            _, data = load_yaml(yaml_path)
            anime = data.get("work", yaml_path.stem)
            for loc in data.get("locations") or []:
                if not loc.get("images"):
                    name = loc.get("name", "?")
                    issues.append(
                        f"[無照片] {anime} / {name}  {DIM}({yaml_path.name}){RESET}"
                    )
    else:
        # Report images on disk not referenced in any YAML
        for subdir in sorted(IMAGES_DIR.iterdir()):
            if not subdir.is_dir():
                continue
            yaml_path = find_yaml_for_dir(subdir.name)
            if yaml_path is None:
                issues.append(
                    f"[無 YAML] {subdir.name}/  → 找不到對應的 {subdir.name}.yaml"
                )
                continue
            _, data = load_yaml(yaml_path)
            referenced = all_referenced_images(data)
            for img in sorted(subdir.iterdir()):
                if img.suffix not in IMAGE_SUFFIXES:
                    continue
                web_path = yaml_image_path(img)
                if web_path not in referenced:
                    issues.append(f"[未引用] {web_path}")

    if issues:
        label = "筆地點沒有照片" if no_images else "個問題"
        print(f"{YELLOW}發現 {len(issues)} {label}：{RESET}\n")
        for line in issues:
            print(f"  {line}")
        if not no_images:
            print(
                f"\n{DIM}執行 `uv run scripts/pilgrimage_images.py batch -i` 互動式加入{RESET}"
            )
        return 1

    msg = "所有地點都有照片" if no_images else "所有照片都已在對應 YAML 中引用"
    print(f"{GREEN}✓ {msg}{RESET}")
    return 0


def cmd_no_gps(unreferenced_only: bool) -> int:
    missing: list[str] = []

    for subdir in sorted(IMAGES_DIR.iterdir()):
        if not subdir.is_dir():
            continue
        referenced: set[str] = set()
        if unreferenced_only:
            yaml_path = find_yaml_for_dir(subdir.name)
            if yaml_path:
                _, data = load_yaml(yaml_path)
                referenced = all_referenced_images(data)
        for img in sorted(subdir.iterdir()):
            if img.suffix not in IMAGE_SUFFIXES:
                continue
            if unreferenced_only and yaml_image_path(img) in referenced:
                continue
            exif = get_exif(img)
            if exif.get("GPSLatitude") is None or exif.get("GPSLongitude") is None:
                missing.append(str(img.relative_to(Path.cwd())))

    if missing:
        print(f"{YELLOW}發現 {len(missing)} 張照片沒有 GPS 資料：{RESET}\n")
        for path in missing:
            print(f"  {path}")
        return 1

    print(f"{GREEN}✓ 所有照片都有 GPS 資料{RESET}")
    return 0


# ── core add logic ────────────────────────────────────────────────────────────


def _add_one(
    image_path: Path,
    yml: YAML,
    data: dict,
    yaml_path: Path,
    dry_run: bool,
    interactive: bool,
) -> bool:
    """Add one image to data. Saves YAML unless dry_run. Returns True if added or already present."""
    web_path = yaml_image_path(image_path)

    if web_path in all_referenced_images(data):
        print(f"  {DIM}已引用，跳過：{image_path.name}{RESET}")
        return True

    if data.get("locations") is None:
        data["locations"] = []

    exif = get_exif(image_path)
    lat = exif.get("GPSLatitude")
    lon = exif.get("GPSLongitude")
    date_raw = exif.get("DateTimeOriginal", "")
    date_str = date_raw[:10].replace(":", "-") if date_raw else None

    best_idx, best_dist = (
        best_location_match(data, lat, lon) if lat and lon else (None, float("inf"))
    )
    loc: dict | None = None

    if best_idx is not None and best_dist <= GPS_MATCH_THRESHOLD_KM:
        loc = data["locations"][best_idx]
        print(
            f"  {GREEN}✓{RESET} {image_path.name} → {loc['name']}  {DIM}({best_dist:.0f} km){RESET}"
        )
    elif interactive:
        loc = pick_location_interactive(data, lat, lon, image_path.name, date_str)
        if loc is None:
            print(f"  {YELLOW}跳過{RESET} {image_path.name}")
            return False
        print(f"  {GREEN}✓{RESET} {image_path.name} → {loc.get('name', '?')}")
    else:
        # Non-interactive fallback: single-location shortcut or placeholder
        locations = data.get("locations") or []
        if lat is None and lon is None and len(locations) == 1:
            loc = locations[0]
            print(
                f"  {GREEN}✓{RESET} {image_path.name} → {loc['name']}  {DIM}(無 GPS，唯一地點){RESET}"
            )
        else:
            reason = (
                f"最近距離 {best_dist:.1f} km" if best_idx is not None else "無 GPS"
            )
            print(
                f"  {YELLOW}⚠{RESET} {image_path.name}：{reason}，建立佔位  {DIM}→ 請手動填寫 {yaml_path.name}{RESET}"
            )
            if not dry_run:
                if lat and lon:
                    _append_placeholder(data, web_path, lat, lon, date_str)
                else:
                    _append_placeholder_no_gps(data, web_path)
            if dry_run:
                print(f"  {DIM}[dry-run] 未寫入{RESET}")
            return True

    if loc is not None:
        if loc.get("images") is None:
            loc["images"] = CommentedSeq()
        loc["images"].append(web_path)

    if dry_run:
        print(f"  {DIM}[dry-run] 未寫入{RESET}")
        return True

    save_yaml(yml, data, yaml_path)
    return True


def _append_placeholder(
    data: dict, web_path: str, lat: float, lon: float, date_str: str | None
) -> None:
    loc: CommentedMap = CommentedMap()
    loc["name"] = "TODO"
    loc["lat"] = round(lat, 6)
    loc["lon"] = round(lon, 6)
    loc["notes"] = ""
    if date_str:
        loc["date"] = date_str
    loc["country"] = "日本"
    loc["city"] = "TODO"
    loc["tags"] = CommentedSeq()
    loc["images"] = CommentedSeq([web_path])
    loc.yaml_set_start_comment("TODO: 補充 name、city 等欄位", indent=2)
    data["locations"].append(loc)


def _append_placeholder_no_gps(data: dict, web_path: str) -> None:
    loc: CommentedMap = CommentedMap()
    loc["name"] = "TODO"
    loc["lat"] = 0.0
    loc["lon"] = 0.0
    loc["notes"] = ""
    loc["country"] = "TODO"
    loc["city"] = "TODO"
    loc["tags"] = CommentedSeq()
    loc["images"] = CommentedSeq([web_path])
    loc.yaml_set_start_comment("TODO: 補充所有欄位（無 GPS 資料）", indent=2)
    data["locations"].append(loc)


# ── add ───────────────────────────────────────────────────────────────────────


def cmd_add(image_path: Path, dry_run: bool, interactive: bool) -> int:
    if not image_path.exists():
        print(f"{RED}錯誤：找不到 {image_path}{RESET}", file=sys.stderr)
        return 1
    if not image_path.is_relative_to(IMAGES_DIR):
        print(f"{RED}錯誤：{image_path} 不在 {IMAGES_DIR}{RESET}", file=sys.stderr)
        return 1

    yaml_path = find_yaml_for_dir(image_path.parent.name)
    if yaml_path is None:
        print(
            f"{RED}錯誤：找不到 {image_path.parent.name}.yaml{RESET}", file=sys.stderr
        )
        return 1

    yml, data = load_yaml(yaml_path)
    _add_one(image_path, yml, data, yaml_path, dry_run, interactive)
    return 0


# ── batch ─────────────────────────────────────────────────────────────────────


def cmd_batch(dry_run: bool, interactive: bool) -> int:
    total = added = skipped = 0

    for subdir in sorted(IMAGES_DIR.iterdir()):
        if not subdir.is_dir():
            continue
        yaml_path = find_yaml_for_dir(subdir.name)
        if yaml_path is None:
            continue
        yml, data = load_yaml(yaml_path)
        referenced = all_referenced_images(data)

        pending = [
            img
            for img in sorted(subdir.iterdir())
            if img.suffix in IMAGE_SUFFIXES and yaml_image_path(img) not in referenced
        ]
        if not pending:
            continue

        print(
            f"\n{BOLD}【{data.get('work', subdir.name)}】{RESET}  {DIM}({len(pending)} 張待加入){RESET}"
        )
        for img in pending:
            total += 1
            ok = _add_one(img, yml, data, yaml_path, dry_run, interactive)
            if ok:
                added += 1
            else:
                skipped += 1

    if total == 0:
        print(f"{GREEN}✓ 沒有待加入的照片{RESET}")
    else:
        print(
            f"\n{BOLD}完成{RESET}：共 {total} 張，加入 {GREEN}{added}{RESET} 張，跳過 {YELLOW}{skipped}{RESET} 張"
        )
    return 0


# ── process wizard (questionary) ─────────────────────────────────────────────

def _next_stem(loc: dict, dest_dir: Path, ext: str) -> str:
    """Return the next available filename stem for a location.

    Derives base from the first existing image (stripping any trailing -N),
    then finds the lowest unused suffix by checking both the YAML images list
    and files on disk.  Pattern: base, base-1, base-2, …
    """
    images = loc.get("images") or []
    if not images:
        return ""

    base = _re.sub(r"-\d+$", "", Path(images[0]).stem)

    taken: set[int] = set()
    for img_path in images:
        stem = Path(img_path).stem
        if stem == base:
            taken.add(0)
        else:
            m = _re.match(rf"^{_re.escape(base)}-(\d+)$", stem)
            if m:
                taken.add(int(m.group(1)))

    for f in dest_dir.glob(f"{base}*{ext}"):
        stem = f.stem
        if stem == base:
            taken.add(0)
        else:
            m = _re.match(rf"^{_re.escape(base)}-(\d+)$", stem)
            if m:
                taken.add(int(m.group(1)))

    if 0 not in taken:
        return base
    n = 1
    while n in taken:
        n += 1
    return f"{base}-{n}"


def _safe_dest(dest_dir: Path, stem: str, ext: str) -> Path:
    """Return a destination Path that does not already exist.

    If stem+ext is taken, appends -1, -2, … until a free slot is found.
    """
    base = _re.sub(r"-\d+$", "", stem)
    candidate = dest_dir / (stem + ext)
    if not candidate.exists():
        return candidate
    n = 1
    while True:
        candidate = dest_dir / f"{base}-{n}{ext}"
        if not candidate.exists():
            return candidate
        n += 1


def _pending_in(directory: Path) -> list[Path]:
    """Return all image files under directory that are not yet referenced in any YAML."""
    pending = []
    for img in sorted(directory.rglob("*")):
        if not img.is_file() or img.suffix not in IMAGE_SUFFIXES:
            continue
        try:
            rel_parts = img.relative_to(IMAGES_DIR).parts
        except ValueError:
            pending.append(img)
            continue
        yaml_path = find_yaml_for_dir(rel_parts[0])
        if yaml_path is None:
            pending.append(img)
            continue
        _, data = load_yaml(yaml_path)
        if yaml_image_path(img) not in all_referenced_images(data):
            pending.append(img)
    return pending


def _q_select_anime(
    lat: float | None, lon: float | None
) -> tuple[Path, YAML, dict] | None:
    import questionary

    entries: list[tuple[float, Path, YAML, dict]] = []
    for p in all_yaml_files():
        yml, data = load_yaml(p)
        dist = best_location_match(data, lat, lon)[1] if lat and lon else float("inf")
        entries.append((dist, p, yml, data))
    entries.sort(key=lambda x: x[0])

    choices = []
    for dist, p, yml, data in entries:
        anime = data.get("work", p.stem)
        suffix = f"  ({dist:.1f} km)" if dist < float("inf") else ""
        marker = " ←" if dist < float("inf") and dist <= GPS_MATCH_THRESHOLD_KM else ""
        choices.append(questionary.Choice(f"{anime}{suffix}{marker}", value=p))
    choices.append(questionary.Choice("跳過", value=None))

    picked_path = questionary.select("選擇系列", choices=choices).ask()
    if picked_path is None:
        return None
    yml2, data2 = load_yaml(picked_path)  # fresh load for editing
    return picked_path, yml2, data2


def _q_pick_location(data: dict, lat: float | None, lon: float | None) -> dict | str:
    import questionary

    locations = data.get("locations") or []
    order = (
        sorted(
            range(len(locations)),
            key=lambda i: (
                haversine_km(lat, lon, locations[i]["lat"], locations[i]["lon"])
                if locations[i].get("lat") is not None
                else float("inf")
            ),
        )
        if lat and lon
        else list(range(len(locations)))
    )

    choices = [questionary.Choice("＋ 新增地點", value="new")]
    for real_i in order:
        loc = locations[real_i]
        label = loc.get("name", "?")
        if lat and lon and loc.get("lat") is not None:
            dist = haversine_km(lat, lon, loc["lat"], loc["lon"])
            marker = " ←" if dist <= GPS_MATCH_THRESHOLD_KM else ""
            label += f"  ({dist:.1f} km{marker})"
        choices.append(questionary.Choice(label, value=loc))
    choices.append(questionary.Choice("跳過此照片", value="skip"))

    result = questionary.select("選擇地點", choices=choices).ask()
    return result if result is not None else "skip"


def _validate_coord(text: str) -> bool | str:
    try:
        float(text)
        return True
    except ValueError:
        return "請輸入有效數字（例：35.1234）"


def _validate_latlng(text: str) -> bool | str:
    try:
        parts = [p.strip() for p in text.replace("，", ",").split(",")]
        if len(parts) != 2:
            raise ValueError
        float(parts[0])
        float(parts[1])
        return True
    except ValueError:
        return "請輸入 lat, lon 格式（例：33.24546, 130.95670）"


def _parse_latlng(text: str) -> tuple[float, float]:
    parts = [p.strip() for p in text.replace("，", ",").split(",")]
    return float(parts[0]), float(parts[1])


def _q_pick_country(data: dict, default: str = "日本") -> str:
    import questionary

    countries = sorted(
        set(
            loc.get("country", "")
            for loc in (data.get("locations") or [])
            if loc.get("country")
        )
    )
    if not countries:
        return questionary.text("國家", default=default).ask() or default

    choices = [questionary.Choice(c, value=c) for c in countries]
    choices.append(questionary.Choice("＋ 新增國家", value="__new__"))

    result = questionary.select("國家", choices=choices).ask()
    if result == "__new__" or result is None:
        new_val = questionary.text("新增國家", default=default).ask()
        return new_val or default
    return result


def _q_pick_city(data: dict, country: str, default: str = "") -> str:
    import questionary

    cities = sorted(
        set(
            loc.get("city", "")
            for loc in (data.get("locations") or [])
            if loc.get("country") == country and loc.get("city")
        )
    )
    if not cities:
        return questionary.text("縣市", default=default).ask() or default

    choices = [questionary.Choice(c, value=c) for c in cities]
    choices.append(questionary.Choice("＋ 新增縣市", value="__new__"))

    result = questionary.select("縣市", choices=choices).ask()
    if result == "__new__" or result is None:
        new_val = questionary.text("新增縣市", default=default).ask()
        return new_val or default
    return result


def _wizard_one(src: Path, idx: int, total: int, dry_run: bool) -> bool:
    import questionary

    print(f"\n{BOLD}{'─' * 48}  {idx}/{total}{RESET}")

    exif = get_exif(src)
    exif_lat = exif.get("GPSLatitude")
    exif_lon = exif.get("GPSLongitude")
    date_raw = exif.get("DateTimeOriginal", "")
    date_str = date_raw[:10].replace(":", "-") if date_raw else None

    rel = src.relative_to(Path.cwd()) if src.is_relative_to(Path.cwd()) else src
    print(f"{BOLD}📷 {rel}{RESET}")
    gps_str = (
        f"{exif_lat:.5f}, {exif_lon:.5f}"
        if exif_lat and exif_lon
        else f"{YELLOW}無 GPS{RESET}"
    )
    print(f"  GPS：{gps_str}    日期：{date_str or f'{YELLOW}無{RESET}'}")
    print()

    # Open photo to review
    if questionary.confirm("開啟照片？", default=True).ask():
        subprocess.run(["open", str(src)], check=False)
        questionary.confirm("看完了，繼續？", default=True).ask()

    # Keep or discard
    if not questionary.confirm("保留此照片？", default=True).ask():
        if questionary.confirm("刪除此照片？", default=False).ask():
            if not dry_run:
                src.unlink()
                print(f"  {RED}已刪除{RESET}")
            else:
                print(f"  {DIM}[dry-run] 將刪除{RESET}")
        return False

    # ── Metadata collection loop (allows retry on wrong input) ──────────────
    while True:
        # Determine anime (use exif GPS for hints only)
        yaml_path = find_yaml_for_dir(src.parent.name)
        if yaml_path:
            yml, data = load_yaml(yaml_path)
            print(f"  系列：{data.get('work')}")
        else:
            result = _q_select_anime(exif_lat, exif_lon)
            if result is None:
                return False
            yaml_path, yml, data = result

        # Pick location (exif GPS used for distance hints only)
        loc_result = _q_pick_location(data, exif_lat, exif_lon)
        if loc_result == "skip" or loc_result is None:
            return False

        is_new = loc_result == "new"
        existing_loc: dict | None = None if is_new else loc_result

        # GPS — only needed for new locations (to store lat/lon)
        gps_comment: str | None = None
        loc_lat, loc_lon = exif_lat, exif_lon

        if is_new:
            if not (exif_lat and exif_lon):
                gps_comment = "no GPS"
                if questionary.confirm("手動輸入 GPS 座標？", default=True).ask():
                    latlng = questionary.text(
                        "GPS（lat, lon）", validate=_validate_latlng
                    ).ask()
                    if latlng:
                        loc_lat, loc_lon = _parse_latlng(latlng)
                        gps_comment = None
                        subprocess.run(
                            ["open", f"maps://?ll={loc_lat},{loc_lon}&q={loc_lat},{loc_lon}"],
                            check=False,
                        )
            else:
                subprocess.run(
                    ["open", f"maps://?ll={exif_lat},{exif_lon}&q={exif_lat},{exif_lon}"],
                    check=False,
                )
                if not questionary.confirm(
                    f"GPS 正確？（{exif_lat:.5f}, {exif_lon:.5f}）", default=True
                ).ask():
                    latlng = questionary.text(
                        "GPS（lat, lon）",
                        default=f"{exif_lat:.5f}, {exif_lon:.5f}",
                        validate=_validate_latlng,
                    ).ask()
                    if latlng:
                        loc_lat, loc_lon = _parse_latlng(latlng)
                        gps_comment = "wrong GPS"

        # Name
        name = questionary.text(
            "地點名稱",
            default=(existing_loc.get("name") or "") if existing_loc else "",
        ).ask()
        if name is None:
            return False
        name = name or (existing_loc.get("name") if existing_loc else "") or "TODO"

        # Filename
        is_heic = src.suffix.lower() == ".heic"
        ext = ".jpg" if is_heic else src.suffix
        dest_dir = IMAGES_DIR / yaml_path.stem
        default_stem = (
            _next_stem(existing_loc, dest_dir, ext) if existing_loc else src.stem
        ) or src.stem
        stem = questionary.text("檔案名稱", default=default_stem).ask()
        if stem is None:
            return False
        stem = stem or default_stem

        # Country (select from existing in this YAML, or add new)
        need_country = is_new or not (existing_loc and existing_loc.get("country"))
        country = (existing_loc.get("country") or "日本") if existing_loc else "日本"
        if need_country:
            country = _q_pick_country(data, default=country)

        # City (select from existing cities for chosen country, or add new)
        need_city = is_new or not (existing_loc and existing_loc.get("city"))
        city = (existing_loc.get("city") or "") if existing_loc else ""
        if need_city:
            city = _q_pick_city(data, country, default=city)

        notes = (existing_loc.get("notes") or "") if existing_loc else ""
        if not notes:
            notes = questionary.text("備註（選填）", default="").ask() or ""

        existing_tags = list(existing_loc.get("tags") or []) if existing_loc else []
        tags_raw = (
            questionary.text(
                "tags（逗號分隔，選填）",
                default="、".join(existing_tags) if existing_tags else "",
            ).ask()
            or ""
        )
        tags = (
            [t.strip() for t in tags_raw.replace("、", ",").split(",") if t.strip()]
            if tags_raw
            else existing_tags
        )

        # Destination — never overwrite
        naive_dest = dest_dir / (stem + ext)
        dest = _safe_dest(dest_dir, stem, ext)
        dest_name = dest.name
        web_path = yaml_image_path(dest)

        # Collect overwrite warnings before showing summary
        overwrite_warnings: list[str] = []
        if naive_dest.exists() and naive_dest.resolve() != dest.resolve():
            overwrite_warnings.append(
                f"{YELLOW}⚠ 檔案 {naive_dest.name} 已存在，已自動改名為 {dest.name}{RESET}"
            )
        if dest.exists() and not (
            src.is_relative_to(IMAGES_DIR) and src.resolve() == dest.resolve()
        ):
            overwrite_warnings.append(
                f"{RED}✗ 目標路徑 {dest.name} 已存在，寫入將覆蓋！{RESET}"
            )
        for loc_entry in data.get("locations") or []:
            if loc_entry is existing_loc:
                continue
            for img in loc_entry.get("images") or []:
                if img == web_path:
                    overwrite_warnings.append(
                        f"{YELLOW}⚠ 圖片路徑 {web_path} 已被其他地點參照{RESET}"
                    )
                    break

        # ── Build or update loc ─────────────────────────────────────────────

        if is_new:
            loc: CommentedMap = CommentedMap()
            loc["name"] = name
            loc["lat"] = round(loc_lat, 6) if loc_lat else 0.0
            loc["lon"] = round(loc_lon, 6) if loc_lon else 0.0
            loc["notes"] = notes
            if date_str:
                loc["date"] = date_str
            loc["country"] = country
            loc["city"] = city
            loc["tags"] = CommentedSeq(tags)
            loc["images"] = CommentedSeq([web_path])
        else:
            loc = existing_loc
            loc["name"] = name
            if city:
                loc["city"] = city
            if country:
                loc["country"] = country
            if notes:
                loc["notes"] = notes
            if tags != existing_tags:
                loc["tags"] = CommentedSeq(tags)
            if date_str:
                existing_date = loc.get("date")
                if existing_date is None:
                    loc["date"] = date_str
                elif isinstance(existing_date, list):
                    existing_date.append(date_str)
                else:
                    loc["date"] = CommentedSeq([str(existing_date), date_str])

        # Summary
        print(f"\n  {BOLD}── 確認 ──{RESET}")
        print(f"  系列：{data.get('work')}")
        print(f"  地點：{name}")
        src_rel = (
            str(src.relative_to(Path.cwd()))
            if src.is_relative_to(Path.cwd())
            else str(src)
        )
        dest_rel = str(dest.relative_to(Path.cwd()))
        if src_rel != dest_rel:
            if is_heic:
                action = "HEIC→JPEG"
            elif src.is_relative_to(IMAGES_DIR):
                action = "重新命名" if src.parent == dest_dir else "移動"
            else:
                action = "複製"
            print(f"  檔案：{Path(src_rel).name} → {dest_rel}  {DIM}({action}){RESET}")
        else:
            print(f"  檔案：{dest_name}")
        if country:
            print(f"  國家：{country}")
        if city:
            print(f"  縣市：{city}")
        if notes:
            print(f"  備註：{notes}")
        if tags:
            print(f"  tags：{', '.join(tags)}")
        if date_str:
            print(f"  日期：{date_str}")
        if overwrite_warnings:
            print()
            for w in overwrite_warnings:
                print(f"  {w}")
        print()

        # Confirm + write (or retry)
        confirm_msg = (
            "確定寫入？（有警告，n = 放棄或重填）" if overwrite_warnings else "寫入？（n = 重新填寫）"
        )
        confirm_default = False if overwrite_warnings else True
        if questionary.confirm(confirm_msg, default=confirm_default).ask():
            break  # proceed to write

        # User said no → offer retry or skip
        if not questionary.confirm("重新填寫此照片？", default=True).ask():
            return False
        # Loop back to location selection
        print(f"\n  {DIM}── 重新填寫 ──{RESET}")

    # ── Write ────────────────────────────────────────────────────────────────
    if not dry_run:
        dest_dir.mkdir(parents=True, exist_ok=True)
        if src.is_relative_to(IMAGES_DIR):
            if src.resolve() != dest.resolve():
                src.rename(dest)
        else:
            if is_heic:
                _heic_to_jpeg(src, dest)
            else:
                shutil.copy2(src, dest)
        if is_new:
            if data.get("locations") is None:
                data["locations"] = []
            data["locations"].append(loc)
        else:
            if not loc.get("images"):
                loc["images"] = CommentedSeq()
            loc["images"].append(web_path)
        if gps_comment:
            images_seq = loc["images"]
            images_seq.yaml_add_eol_comment(gps_comment, len(images_seq) - 1)
        save_yaml(yml, data, yaml_path)
        print(f"  {GREEN}✓ 已寫入{RESET}")
    else:
        print(f"  {DIM}[dry-run] 未寫入{RESET}")

    return True


def cmd_process(paths: list[Path], dry_run: bool) -> int:
    import questionary

    pending: list[Path] = []
    for path in paths:
        path = path.resolve()
        if path.is_dir():
            pending.extend(_pending_in(path))
        elif path.is_file():
            if path.suffix in IMAGE_SUFFIXES:
                pending.append(path)
            else:
                print(f"{YELLOW}略過（不支援格式）：{path.name}{RESET}")
        else:
            print(f"{RED}找不到：{path}{RESET}", file=sys.stderr)

    # Deduplicate while preserving order
    seen: set[Path] = set()
    pending = [p for p in pending if not (p in seen or seen.add(p))]  # type: ignore[func-returns-value]

    if not pending:
        print(f"{GREEN}✓ 沒有待處理的照片{RESET}")
        return 0

    # Step 1+2: list all pending photos with GPS and date
    print(f"\n{BOLD}待處理照片（{len(pending)} 張）：{RESET}\n")
    for img in pending:
        exif = get_exif(img)
        rel = img.relative_to(Path.cwd()) if img.is_relative_to(Path.cwd()) else img
        gps_str = (
            f"{exif['GPSLatitude']:.4f}, {exif['GPSLongitude']:.4f}"
            if exif.get("GPSLatitude")
            else f"{YELLOW}無 GPS{RESET}"
        )
        date_raw = exif.get("DateTimeOriginal", "")
        date_str = (
            date_raw[:10].replace(":", "-") if date_raw else f"{YELLOW}無日期{RESET}"
        )
        print(f"  {rel}")
        print(f"  {DIM}GPS：{gps_str}    日期：{date_str}{RESET}")
        print()

    if not questionary.confirm(f"開始處理 {len(pending)} 張？", default=True).ask():
        return 0

    done = skipped = 0
    for i, src in enumerate(pending, start=1):
        ok = _wizard_one(src, i, len(pending), dry_run)
        if ok:
            done += 1
        else:
            skipped += 1

    print(
        f"\n{BOLD}完成{RESET}：處理 {GREEN}{done}{RESET} 張，跳過 {YELLOW}{skipped}{RESET} 張"
    )
    return 0


# ── heic conversion ───────────────────────────────────────────────────────────


def _heic_to_jpeg(src: Path, dest: Path) -> None:
    """Convert HEIC to JPEG using pillow-heif, converting to sRGB and preserving EXIF."""
    from PIL import Image
    from pillow_heif import register_heif_opener

    register_heif_opener()

    img = Image.open(src)
    exif = img.getexif()
    # Convert to RGB (drops wide-gamut P3 profile → plain sRGB JPEG)
    if img.mode != "RGB":
        img = img.convert("RGB")
    img.save(dest, "JPEG", quality=92, exif=exif.tobytes() if exif else b"")


# ── main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    check_p = sub.add_parser("check", help="列出未在 YAML 中引用的照片，或地點缺少照片")
    check_p.add_argument(
        "--no-images", "-n", action="store_true", help="列出 YAML 裡沒有照片的地點"
    )
    no_gps_p = sub.add_parser("no-gps", help="列出沒有 GPS 資料的照片")
    no_gps_p.add_argument(
        "--unreferenced", "-u", action="store_true", help="只顯示尚未加入 YAML 的照片"
    )

    add_p = sub.add_parser(
        "add", help="將單張照片加入對應 YAML（照片必須已在正確目錄）"
    )
    add_p.add_argument("image", type=Path, help="照片路徑")
    add_p.add_argument("--dry-run", action="store_true")
    add_p.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="GPS 無法自動比對時互動選擇地點",
    )

    batch_p = sub.add_parser("batch", help="批次加入所有未引用照片")
    batch_p.add_argument("--dry-run", action="store_true")
    batch_p.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="GPS 無法自動比對時互動選擇地點",
    )

    proc_p = sub.add_parser(
        "process",
        help="互動式精靈：接受目錄或照片路徑（可混用），預設掃描全部",
    )
    proc_p.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[IMAGES_DIR],
        help="目錄或照片路徑，可混用（預設：掃描所有 pilgrimage 目錄）",
    )
    proc_p.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    if args.cmd == "check":
        sys.exit(cmd_check(no_images=args.no_images))
    elif args.cmd == "no-gps":
        sys.exit(cmd_no_gps(args.unreferenced))
    elif args.cmd == "add":
        sys.exit(cmd_add(args.image.resolve(), args.dry_run, args.interactive))
    elif args.cmd == "batch":
        sys.exit(cmd_batch(args.dry_run, args.interactive))
    elif args.cmd == "process":
        sys.exit(cmd_process(args.paths, args.dry_run))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""story-ranking 殘酷二選一配對比較排序工具.

Usage:
    uv run python scripts/story_ranking_sort.py [--file <name>] [--tier <T>] [--resume]
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from rich.console import Console
from rich.markup import escape as markup_escape
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from ruamel.yaml import YAML

# --------------------------------------------------------------------------- #
# Constants — single source of truth
# --------------------------------------------------------------------------- #

TIER_ORDER = ["SSS", "SS", "S", "A", "B", "C", "D", "E", "F", "G"]
TIER_SCORE = {t: len(TIER_ORDER) - i for i, t in enumerate(TIER_ORDER)}

TIER_FILES = [
    "anime",
    "live-action-movie",
    "live-action-tv",
    "manga-completed",
    "manga-ongoing",
    "novel",
]
NO_TIER_FILES = ["documentary", "artbook", "other"]
GROUP_FILES = ["star-wars"]

REPO_ROOT = Path(__file__).parent.parent
YAML_DIR = REPO_ROOT / "content" / "data" / "story-ranking"
CACHE_DIR = Path(__file__).parent / ".story_ranking_sort_cache"

console = Console()


# --------------------------------------------------------------------------- #
# YAML helpers
# --------------------------------------------------------------------------- #


def load_yaml_safe(file: str) -> list[dict[str, Any]]:
    """Load YAML using yaml.safe_load for reading."""
    path = YAML_DIR / f"{file}.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return raw or []


def detect_file_type(entries: list[dict]) -> str:
    """Return 'tier', 'group', or 'notier'."""
    for e in entries:
        if "tier" in e:
            return "tier"
        if "group" in e:
            return "group"
    return "notier"


# --------------------------------------------------------------------------- #
# Session cache
# --------------------------------------------------------------------------- #


def cache_path(file: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{file}.json"


def load_cache(file: str) -> dict:
    p = cache_path(file)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


def save_cache(file: str, data: dict) -> None:
    data["updated_at"] = datetime.now(tz=timezone.utc).isoformat()
    cache_path(file).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def clear_cache(file: str) -> None:
    p = cache_path(file)
    if p.exists():
        p.unlink()


# --------------------------------------------------------------------------- #
# Merge sort by human
# --------------------------------------------------------------------------- #


class HumanMergeSort:
    """Merge sort delegating comparisons to a human via Rich TUI."""

    def __init__(
        self,
        items: list[tuple[str, str]],  # [(title, tier), ...]
        known: dict[str, int] | None = None,
        file: str = "",
        tier_filter: str | None = None,
    ) -> None:
        self.items = items
        # known comparisons: key = "A|||B" -> 1 if A wins, -1 if B wins
        self.known: dict[str, int] = known or {}
        self.file = file
        self.tier_filter = tier_filter
        self.comparison_count = 0
        self.history: list[tuple[str, str, int]] = []  # (a, b, result)
        # Estimate total comparisons: n log2 n
        n = len(items)
        import math
        self.estimated_total = int(n * math.log2(n)) if n > 1 else 0
        self.aborted = False
        self.apply_now = False

    def _cmp_key(self, a: str, b: str) -> str:
        return f"{a}|||{b}"

    def _compare(self, a: tuple[str, str], b: tuple[str, str]) -> int:
        """Return 1 if a > b (a wins), -1 if b > a (b wins).

        Positive = a should rank higher (comes first in sorted list).
        """
        # Same tier → treat as equal, skip human input (改動 3)
        if a[1] == b[1]:
            return 0

        key_ab = self._cmp_key(a[0], b[0])
        key_ba = self._cmp_key(b[0], a[0])

        if key_ab in self.known:
            return self.known[key_ab]
        if key_ba in self.known:
            return -self.known[key_ba]

        # Need human input
        while True:
            console.clear()

            done = self.comparison_count
            est = self.estimated_total
            tier_label = f" · 篩選 tier: {self.tier_filter}" if self.tier_filter else ""
            console.print(Panel(
                f"[dim]已比較 [bold]{done}[/bold] 組，預估總計 ~{est} 組{tier_label}[/dim]\n"
                "[dim]比較完成後可以重新分配 tier（或直接維持現有分佈），再寫回 YAML[/dim]",
                title="[bold cyan]story-ranking 排序[/bold cyan]",
            ))

            k1, k2, ks, ku, kq = (
                markup_escape("[1]"), markup_escape("[2]"), markup_escape("[s]"),
                markup_escape("[u]"), markup_escape("[q]"),
            )

            table = Table(show_header=True, header_style="bold magenta", expand=True)
            table.add_column(f"{k1} 左邊", style="cyan", ratio=1)
            table.add_column(f"{k2} 右邊", style="green", ratio=1)
            table.add_row(
                f"[bold]{markup_escape(a[0])}[/bold]",
                f"[bold]{markup_escape(b[0])}[/bold]",
            )
            console.print(table)

            console.print(Panel(
                f"[cyan]{k1}[/cyan] 左邊更好   [green]{k2}[/green] 右邊更好   "
                f"[yellow]{ks}[/yellow] 跳過這題   [blue]{ku}[/blue] 撤回上一題   "
                f"[red]{kq}[/red] 存檔離開",
                title="操作",
                expand=False,
            ))

            try:
                choice = Prompt.ask("選擇", default="").strip().lower()
            except (KeyboardInterrupt, EOFError):
                choice = "q"

            if choice == "1":
                result = 1
                self.known[key_ab] = result
                self.history.append((a[0], b[0], result))
                self.comparison_count += 1
                return result
            elif choice == "2":
                result = -1
                self.known[key_ab] = result
                self.history.append((a[0], b[0], result))
                self.comparison_count += 1
                return result
            elif choice == "s":
                # Skip: treat as equal, don't record
                return 0
            elif choice == "u":
                if self.history:
                    last_a, last_b, _ = self.history.pop()
                    last_key = self._cmp_key(last_a, last_b)
                    self.known.pop(last_key, None)
                    self.known.pop(self._cmp_key(last_b, last_a), None)
                    self.comparison_count = max(0, self.comparison_count - 1)
                    console.print("[yellow]已撤回上一次選擇。[/yellow]")
                    # Re-ask current pair
                    continue
                else:
                    console.print("[dim]沒有可撤回的操作。[/dim]")
                    continue
            elif choice == "q":
                self.aborted = True
                return 0
            else:
                console.print("[red]請輸入 1、2、s、u 或 q[/red]")

    def _merge(self, left: list, right: list) -> list:
        result = []
        i = j = 0
        while i < len(left) and j < len(right):
            if self.aborted or self.apply_now:
                result.extend(left[i:])
                result.extend(right[j:])
                return result
            cmp = self._compare(left[i], right[j])
            if cmp >= 0:
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1
        result.extend(left[i:])
        result.extend(right[j:])
        return result

    def _merge_sort(self, items: list) -> list:
        if len(items) <= 1:
            return items
        mid = len(items) // 2
        left = self._merge_sort(items[:mid])
        right = self._merge_sort(items[mid:])
        return self._merge(left, right)

    def sort(self) -> list[tuple[str, str]]:
        """Run merge sort. Returns sorted list (best first)."""
        return self._merge_sort(self.items[:])


# --------------------------------------------------------------------------- #
# Tier mapping
# --------------------------------------------------------------------------- #


def assign_tiers_keep_distribution(
    sorted_items: list[tuple[str, str]],
    original_tiers: list[str],
) -> list[tuple[str, str, str]]:
    """Assign tiers keeping the original distribution.

    sorted_items: best-first order [(title, old_tier)]
    original_tiers: sorted list of tiers used in original data (best-first)
    Returns: [(title, old_tier, new_tier)]
    """
    # Count how many were in each tier originally
    tier_counts: dict[str, int] = {}
    for _, t in sorted_items:
        tier_counts[t] = tier_counts.get(t, 0) + 1

    # Build assignment order using original tier distribution
    assignment: list[str] = []
    for tier in original_tiers:
        count = tier_counts.get(tier, 0)
        assignment.extend([tier] * count)

    result = []
    for i, (title, old_tier) in enumerate(sorted_items):
        new_tier = assignment[i] if i < len(assignment) else old_tier
        result.append((title, old_tier, new_tier))
    return result


def assign_tiers_equal(
    sorted_items: list[tuple[str, str]],
    tier_range: list[str],
) -> list[tuple[str, str, str]]:
    """Evenly distribute sorted items across tier_range."""
    n = len(sorted_items)
    k = len(tier_range)
    result = []
    for i, (title, old_tier) in enumerate(sorted_items):
        tier_idx = min(int(i * k / n), k - 1)
        new_tier = tier_range[tier_idx]
        result.append((title, old_tier, new_tier))
    return result


def show_ranking(sorted_items: list[tuple[str, str]]) -> None:
    """Display the current ranking result."""
    console.clear()
    console.print(Panel("[bold green]排序完成！以下是你比較出來的名次[/bold green]", expand=False))
    table = Table(show_header=True, header_style="bold", expand=True)
    table.add_column("名次", style="dim", width=5)
    table.add_column("作品", ratio=4)
    table.add_column("目前 Tier", style="yellow", width=10)
    for i, (title, tier) in enumerate(sorted_items, 1):
        table.add_row(str(i), markup_escape(title), tier)
    console.print(table)


def interactive_tier_assignment(
    sorted_items: list[tuple[str, str]],
    original_tiers: list[str],
) -> list[tuple[str, str, str]] | None:
    """Show ranking + proposed tier changes, ask whether to proceed. Returns None to skip."""
    show_ranking(sorted_items)

    assignments = assign_tiers_keep_distribution(sorted_items, original_tiers)
    changed = [(t, o, n) for t, o, n in assignments if o != n]

    console.print()
    if not changed:
        console.print("[dim]依目前排名，所有作品的 tier 維持不變。[/dim]")
        return None

    console.print(
        f"[dim]依目前排名，保持各 tier 現有數量，以下 [bold]{len(changed)}[/bold] 部作品的 tier 會改動：[/dim]"
    )
    table = Table(show_header=True, header_style="bold", expand=False)
    table.add_column("作品", ratio=4)
    table.add_column("目前", style="yellow", width=8)
    table.add_column("→", style="dim", width=3)
    table.add_column("建議", style="green", width=8)
    for title, old, new in changed:
        table.add_row(markup_escape(title), old, "→", new)
    console.print(table)
    console.print()

    try:
        ok = Confirm.ask("套用這些改動？", default=False)
    except (KeyboardInterrupt, EOFError):
        ok = False
    return assignments if ok else None


# --------------------------------------------------------------------------- #
# Session status display
# --------------------------------------------------------------------------- #


def _find_conflicts(known: dict[str, int]) -> list[tuple[str, str]]:
    """Return pairs (a, b) where both a>b and b>a are implied by known comparisons."""
    # Build adjacency: wins[a] = set of titles a beats
    wins: dict[str, set[str]] = {}
    for key, result in known.items():
        parts = key.split("|||", 1)
        if len(parts) != 2:
            continue
        a, b = parts
        if result == 1:
            wins.setdefault(a, set()).add(b)
        elif result == -1:
            wins.setdefault(b, set()).add(a)

    # For each known direct comparison, check if the loser transitively beats the winner
    conflicts = []
    for key, result in known.items():
        parts = key.split("|||", 1)
        if len(parts) != 2:
            continue
        a, b = parts
        winner, loser = (a, b) if result == 1 else (b, a)
        # BFS: can loser reach winner through wins?
        visited: set[str] = set()
        queue = list(wins.get(loser, set()))
        found = False
        while queue and not found:
            node = queue.pop()
            if node == winner:
                found = True
                break
            if node not in visited:
                visited.add(node)
                queue.extend(wins.get(node, set()) - visited)
        if found:
            conflicts.append((winner, loser))
    return conflicts


def show_session_status(
    sorter: "HumanMergeSort",
    all_items: list[tuple[str, str]],
) -> None:
    """Show this session's choices, contradictions, and current tier of all items."""
    console.clear()
    console.rule("[bold]Session 結果")

    # 建立 title -> tier 查表
    tier_map = {title: tier for title, tier in all_items}

    # --- 本次選擇 ---
    console.print(f"\n本次 [bold]{sorter.comparison_count}[/bold] 次選擇：\n")
    if sorter.history:
        choice_table = Table(show_header=False, expand=False, box=None, padding=(0, 1))
        choice_table.add_column("winner", style="green")
        choice_table.add_column("winner_tier", style="dim", width=5)
        choice_table.add_column("sym", style="dim", width=3)
        choice_table.add_column("loser", style="dim")
        choice_table.add_column("loser_tier", style="dim", width=5)
        for a, b, result in sorter.history:
            winner, loser = (a, b) if result == 1 else (b, a)
            wt = tier_map.get(winner, "?")
            lt = tier_map.get(loser, "?")
            choice_table.add_row(
                markup_escape(winner), f"[{wt}]",
                ">",
                markup_escape(loser), f"[{lt}]",
            )
        console.print(choice_table)
    else:
        console.print("[dim]（尚無選擇）[/dim]")

    # --- 矛盾偵測 ---
    console.print()
    conflicts = _find_conflicts(sorter.known)
    if conflicts:
        console.print(f"[bold red]⚠ 偵測到 {len(conflicts)} 個矛盾（傳遞循環）：[/bold red]")
        for w, loser in conflicts:
            wt = tier_map.get(w, "?")
            lt = tier_map.get(loser, "?")
            console.print(
                f"  [red]{markup_escape(w)} [{wt}] > {markup_escape(loser)} [{lt}][/red]"
                "（但存在反向傳遞關係）"
            )
    else:
        console.print("[green]✓ 選擇無矛盾[/green]")
    console.print()


# --------------------------------------------------------------------------- #
# Dry-run diff display
# --------------------------------------------------------------------------- #


def show_diff(assignments: list[tuple[str, str, str]]) -> None:
    """Print dry-run diff table."""
    console.print()
    console.rule("[bold]Dry-run 預覽")
    table = Table(show_header=True, header_style="bold")
    table.add_column("#", style="dim", width=4)
    table.add_column("Title", ratio=3)
    table.add_column("舊 Tier", style="yellow", width=8)
    table.add_column("新 Tier", style="green", width=8)
    table.add_column("", width=4)

    for i, (title, old_tier, new_tier) in enumerate(assignments, 1):
        changed = old_tier != new_tier
        marker = "[bold red]![/bold red]" if changed else ""
        table.add_row(str(i), title, old_tier, new_tier, marker)

    console.print(table)

    changed_count = sum(1 for _, o, n in assignments if o != n)
    console.print(f"[dim]共 {len(assignments)} 項，其中 {changed_count} 項 tier 變更[/dim]")


# --------------------------------------------------------------------------- #
# ruamel.yaml write-back
# --------------------------------------------------------------------------- #


def write_back(file: str, assignments: list[tuple[str, str, str]]) -> None:
    """Write updated tiers and reorder entries using ruamel.yaml round-trip."""
    path = YAML_DIR / f"{file}.yaml"
    ryaml = YAML()
    ryaml.preserve_quotes = True
    ryaml.default_flow_style = False

    with path.open(encoding="utf-8") as f:
        data = ryaml.load(f)

    # Build lookup: title -> new_tier
    new_tier_map = {title: new_tier for title, _, new_tier in assignments}

    # Update tier values in-place first
    for entry in data:
        title = entry.get("title", "")
        if title in new_tier_map and "tier" in entry:
            entry["tier"] = new_tier_map[title]

    # Build title -> rank (from assignments order, best=0)
    rank_map = {title: i for i, (title, _, _) in enumerate(assignments)}

    # Group entries by new tier, maintaining rank within each tier
    tier_groups: dict[str, list] = {t: [] for t in TIER_ORDER}
    ungrouped = []

    for entry in data:
        title = entry.get("title", "")
        new_tier = new_tier_map.get(title)
        if new_tier and new_tier in tier_groups:
            tier_groups[new_tier].append((rank_map.get(title, 9999), entry))
        else:
            ungrouped.append(entry)

    # Sort within each tier by rank
    for t in TIER_ORDER:
        tier_groups[t].sort(key=lambda x: x[0])

    # Reconstruct ordered list
    new_data = []
    for t in TIER_ORDER:
        new_data.extend(e for _, e in tier_groups[t])
    new_data.extend(ungrouped)

    # Replace data contents (preserve CommentedSeq type)
    data.clear()
    data.extend(new_data)

    with path.open("w", encoding="utf-8") as f:
        ryaml.dump(data, f)

    console.print(f"[green]已寫回 {path.name}[/green]")


# --------------------------------------------------------------------------- #
# File selection
# --------------------------------------------------------------------------- #


def select_file_interactive() -> str:
    """Show Rich menu to select a tier file."""
    console.print()
    console.print(Panel("[bold]選擇要排序的檔案[/bold]"))
    for i, name in enumerate(TIER_FILES, 1):
        console.print(f"  [{i}] {name}")

    while True:
        try:
            choice = Prompt.ask("輸入編號").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]已取消。[/yellow]")
            sys.exit(0)

        if choice.isdigit() and 1 <= int(choice) <= len(TIER_FILES):
            return TIER_FILES[int(choice) - 1]
        console.print(f"[red]請輸入 1~{len(TIER_FILES)} 的數字[/red]")


# --------------------------------------------------------------------------- #
# Main flow
# --------------------------------------------------------------------------- #


def main() -> None:
    parser = argparse.ArgumentParser(description="story-ranking 殘酷二選一排序工具")
    parser.add_argument("--file", "-f", help="YAML 名稱（不含路徑和副檔名，如 anime）")
    parser.add_argument("--tier", "-t", help="只比較指定 tier 的作品（如 SS）")
    parser.add_argument("--resume", action="store_true", help="接續上次未完成的 session")
    args = parser.parse_args()

    # Select file
    file = args.file
    if not file:
        file = select_file_interactive()

    yaml_path = YAML_DIR / f"{file}.yaml"
    if not yaml_path.exists():
        console.print(f"[red]找不到檔案：{yaml_path}[/red]")
        sys.exit(1)

    entries = load_yaml_safe(file)
    file_type = detect_file_type(entries)

    if file_type in ("notier", "group"):
        label = "group 欄位" if file_type == "group" else "tier 欄位"
        console.print(
            f"[yellow]此檔（{file}.yaml）無 {label}，"
            "可比較順序但不寫入 tier 值。[/yellow]"
        )
        try:
            ok = Confirm.ask("是否繼續？", default=False)
        except (KeyboardInterrupt, EOFError):
            ok = False
        if not ok:
            console.print("[dim]已取消。[/dim]")
            sys.exit(0)

    # Filter by tier
    tier_filter = args.tier
    if tier_filter and tier_filter not in TIER_ORDER:
        console.print(f"[red]未知的 tier：{tier_filter}，可用：{' '.join(TIER_ORDER)}[/red]")
        sys.exit(1)

    # Extract items
    all_items: list[tuple[str, str]] = []
    for e in entries:
        title = e.get("title", "")
        tier = e.get("tier", e.get("group", "?"))
        if tier_filter and tier != tier_filter:
            continue
        all_items.append((title, tier))

    if not all_items:
        console.print("[yellow]沒有符合條件的項目。[/yellow]")
        sys.exit(0)

    console.print(
        f"\n[bold]檔案[/bold]: {file}.yaml  |  "
        f"[bold]項目數[/bold]: {len(all_items)}"
        + (f"  |  [bold]Tier 篩選[/bold]: {tier_filter}" if tier_filter else "")
    )

    # Load or init session cache
    cache_file = f"{file}" + (f"__{tier_filter}" if tier_filter else "")

    known: dict[str, int] = {}
    if args.resume:
        cache_data = load_cache(cache_file)
        if cache_data.get("known"):
            known = cache_data["known"]
            console.print(
                f"[dim]已載入上次 session，"
                f"已知比較 {len(known)} 組（{cache_data.get('updated_at', '')}）[/dim]"
            )
        else:
            console.print("[dim]沒有找到上次的 session，從頭開始。[/dim]")

    # Randomise initial order so merge sort makes more cross-tier comparisons (改動 4)
    random.shuffle(all_items)

    # Run sort
    sorter = HumanMergeSort(all_items, known=known, file=cache_file, tier_filter=tier_filter)

    console.print()
    console.print(Panel(
        "[bold cyan]開始比較！[/bold cyan]\n"
        "每輪選出你覺得「更好」的作品。",
        title="story-ranking 排序"
    ))

    try:
        sorter.sort()
    except KeyboardInterrupt:
        sorter.aborted = True

    # Save cache
    save_cache(cache_file, {
        "file": file,
        "tier_filter": tier_filter,
        "known": sorter.known,
        "comparison_count": sorter.comparison_count,
    })

    show_session_status(sorter, all_items)
    console.print("[dim]Session 已存檔，下次用 --resume 繼續。[/dim]")


if __name__ == "__main__":
    main()

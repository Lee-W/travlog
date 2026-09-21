"""Build the searchable catalog from the authoritative ranking YAML files."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import yaml

CATEGORIES = {
    "anime": ("動畫", "アニメ"),
    "live-action-movie": ("真人電影", "実写映画"),
    "live-action-tv": ("真人影集", "実写ドラマ"),
    "documentary": ("紀錄片", "ドキュメンタリー"),
    "star-wars": ("星際大戰", "スター・ウォーズ"),
    "manga-completed": ("完結漫畫", "完結した漫画"),
    "manga-ongoing": ("連載漫畫", "連載中の漫画"),
    "novel": ("小說", "小説"),
    "artbook": ("設定集", "設定資料集"),
}
# Tier text also lives in content/pages/story-ranking.md and -ja.md's
# comparison tables. Changing one requires changing the other three.
TIERS = {
    "SSS": ("無可撼動，沒有之一", "揺るがない、これ以外にない"),
    "SS": ("神作", "神作"),
    "S": ("佳作以上，神作未滿", "良作以上、神作未満"),
    "A": ("蠻喜歡的佳作", "かなり好きな良作"),
    "B": ("還算蠻好看的", "わりとおもしろかった"),
    "C": ("普通，或優缺點相抵", "ふつう、または長所と短所が相殺"),
    "D": ("不喜歡", "好きではない"),
    "E": ("看得有點痛苦", "観ていて少しつらい"),
    "F": ("看得真的很痛苦", "観ていて本当につらい"),
    "G": (
        "你不一定要看，但一定要推薦給你朋友",
        "観なくてもいいけれど、友達には絶対すすめたい",
    ),
}
RANKS = {tier: len(TIERS) - index for index, tier in enumerate(TIERS)}


def build_database(source: Path) -> list[dict]:
    """Preserve every entry and review; never deduplicate by work title."""
    found = {path.stem for path in source.glob("*.yaml")}
    if found != CATEGORIES.keys():
        raise ValueError(
            f"Ranking categories changed: missing={sorted(CATEGORIES.keys() - found)}, "
            f"unknown={sorted(found - CATEGORIES.keys())}"
        )
    result = []
    for category in CATEGORIES:
        rows = yaml.safe_load((source / f"{category}.yaml").read_text(encoding="utf-8"))
        if not isinstance(rows, list):
            raise TypeError(f"{category}: expected a list of ranking entries")
        for row in rows:
            tier = row.get("tier") or "unranked"
            if tier != "unranked" and tier not in TIERS:
                raise ValueError(f"{category}: unknown tier {tier!r}")
            reviews = deepcopy(row.get("reviews", []))
            result.append(
                {
                    "title": row["title"],
                    "title_zh": deepcopy(row["title"]),
                    # build_ja_data promotes this title and keeps the original
                    # in title_zh, so either language remains searchable.
                    "title_native": row.get("title_native", ""),
                    "category": category,
                    "tier": tier,
                    "rank": RANKS.get(tier),
                    "reviews": reviews,
                    "has_review": "yes" if reviews else "no",
                }
            )
    return result


def view_config(lang: str) -> dict:
    """Keep the filter values stable across the two language versions."""
    index = {"zh-tw": 0, "ja": 1}[lang]
    original_title = "title_native" if index == 0 else "title_zh"
    return {
        "fields": ["title", "category", "tier", "reviews"],
        "field_labels": {
            "title": ("作品名稱", "作品名")[index],
            "category": ("分類", "分類")[index],
            "tier": "Tier",
            "reviews": ("評論", "感想")[index],
            "rank": ("喜好程度", "好み順")[index],
            "has_review": ("評論收錄", "感想の有無")[index],
        },
        "search_fields": ["title", original_title],
        "sort_fields": ["rank", "title"],
        "field_types": {"rank": "number", "title": "text"},
        "sort_by": "rank",
        "sort_order": "desc",
        "filters": {
            "category": {
                "options": [
                    {"value": key, "label": labels[index]}
                    for key, labels in CATEGORIES.items()
                ]
            },
            "tier": {
                "options": [
                    {
                        "value": tier,
                        "label": tier,
                        "description": descriptions[index],
                        "tone": "green" if tier in {"SSS", "SS"} else "neutral",
                    }
                    for tier, descriptions in TIERS.items()
                ]
                + [{"value": "unranked", "label": ("未分級", "Tier なし")[index]}]
            },
            "has_review": {
                "options": [
                    {"value": "yes", "label": ("有評論", "感想あり")[index]},
                    {"value": "no", "label": ("尚無評論", "感想なし")[index]},
                ]
            },
        },
        "display": {
            "layout": "responsive",
            "title_field": "title",
            "meta_fields": ["category", "tier", "reviews"],
            "legend_fields": ["tier"],
        },
        "messages": {
            "search": ("搜尋作品名稱或原名…", "作品名・原題を検索…")[index],
            "empty": ("沒有符合條件的作品。", "条件に合う作品はありません。")[index],
            "count": ("{shown} / {total} 筆紀錄", "{shown} / {total} 件")[index],
            "legend": ("分級說明", "説明")[index],
            "clear_search": ("清除", "クリア")[index],
            "clear": ("重設", "リセット")[index],
        },
        "query_sync": True,
    }


def main() -> None:
    rows = build_database(Path("content/data/story-ranking"))
    output = Path("content/data/story-database.yaml")
    output.write_text(
        yaml.safe_dump(rows, allow_unicode=True, sort_keys=False, width=1000),
        encoding="utf-8",
    )
    print(f"story database: {len(rows)} entries from {len(CATEGORIES)} categories")


if __name__ == "__main__":
    main()

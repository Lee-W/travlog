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
            translations = deepcopy(row.get("translations", {}))
            reviews = deepcopy(row.get("reviews", []))
            result.append(
                {
                    "title": row["title"],
                    "title_zh": deepcopy(row["title"]),
                    "translations": translations,
                    # Flat search aliases survive Tabular's display projection,
                    # which removes the translation mapping before indexing.
                    "title_ja": translations.get("ja", {}).get("title", ""),
                    "category": category,
                    "tier": tier,
                    "rank": RANKS.get(tier),
                    "reviews": reviews,
                    "has_review": "yes" if reviews else "no",
                }
            )
    return result


def view_config() -> dict:
    """One config for both languages; the plugin picks the text per component.

    Filter values stay canonical (`anime`, `SSS`, `yes`) so the query string
    and cross-language links keep working; only their labels are localized.
    """
    return {
        "fields": ["title", "category", "tier", "reviews"],
        "field_labels": {
            "title": {"zh-TW": "作品名稱", "ja": "作品名"},
            "category": {"zh-TW": "分類", "ja": "分類"},
            "tier": "Tier",
            "reviews": {"zh-TW": "評論", "ja": "感想"},
            "rank": {"zh-TW": "喜好程度", "ja": "好み順"},
            "has_review": {"zh-TW": "評論收錄", "ja": "感想の有無"},
        },
        # On the ja component `title` becomes the original title. The plugin
        # projects rows before it builds the search index, so searching the
        # displayed `title` would only ever find that component's language.
        # The two canonical spellings are indexed instead, which covers both
        # languages on both subsites without indexing the same text twice.
        "translations": {
            "fields": ["title"],
            "source_lang": "zh-TW",
        },
        "search_fields": ["title_zh", "title_ja"],
        "sort_fields": ["rank", "title"],
        "field_types": {"rank": "number", "title": "text"},
        "sort_by": "rank",
        "sort_order": "desc",
        "filters": {
            "category": {
                "options": [
                    {"value": key, "label": {"zh-TW": zh, "ja": ja}}
                    for key, (zh, ja) in CATEGORIES.items()
                ]
            },
            "tier": {
                "options": [
                    {
                        "value": tier,
                        "label": tier,
                        "description": {"zh-TW": zh, "ja": ja},
                        "tone": "green" if tier in {"SSS", "SS"} else "neutral",
                    }
                    for tier, (zh, ja) in TIERS.items()
                ]
                + [
                    {
                        "value": "unranked",
                        "label": {"zh-TW": "未分級", "ja": "Tier なし"},
                    }
                ]
            },
            "has_review": {
                "options": [
                    {"value": "yes", "label": {"zh-TW": "有評論", "ja": "感想あり"}},
                    {"value": "no", "label": {"zh-TW": "尚無評論", "ja": "感想なし"}},
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
            "search": {"zh-TW": "搜尋作品名稱或原名…", "ja": "作品名・原題を検索…"},
            "empty": {
                "zh-TW": "沒有符合條件的作品。",
                "ja": "条件に合う作品はありません。",
            },
            "count": {
                "zh-TW": "{shown} / {total} 筆紀錄",
                "ja": "{shown} / {total} 件",
            },
            "legend": {"zh-TW": "分級說明", "ja": "説明"},
            "clear_search": {"zh-TW": "清除", "ja": "クリア"},
            "clear": {"zh-TW": "重設", "ja": "リセット"},
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

import tempfile
import unittest
from pathlib import Path

from scripts.check_anilist_story_ranking import (
    RankingEntry,
    load_ranking_entries,
    validate,
)


def media_entry(media_id, score, media_type="ANIME", media_format="TV"):
    return {
        "status": "COMPLETED",
        "score": score,
        "media": {
            "id": media_id,
            "type": media_type,
            "format": media_format,
            "title": {
                "romaji": f"Media {media_id}",
                "english": None,
                "native": None,
            },
        },
    }


class AniListStoryRankingTest(unittest.TestCase):
    def test_validate_accepts_bidirectional_mapping(self):
        ranking = [RankingEntry("anime.yaml", "Example", "S", "ANIME", (1,))]
        collections = {"ANIME": {1: media_entry(1, 8)}, "MANGA": {}}

        self.assertEqual(validate(ranking, collections), [])

    def test_validate_rejects_score_drift(self):
        ranking = [RankingEntry("anime.yaml", "Example", "S", "ANIME", (1,))]
        collections = {"ANIME": {1: media_entry(1, 7)}, "MANGA": {}}

        errors = validate(ranking, collections)

        self.assertTrue(any("expects score 8" in error for error in errors))

    def test_validate_rejects_reverse_drift(self):
        collections = {"ANIME": {1: media_entry(1, 8)}, "MANGA": {}}

        errors = validate([], collections)

        self.assertTrue(any("no story-ranking mapping" in error for error in errors))

    def test_validate_accepts_duplicate_id_for_multiple_ranking_entries(self):
        ranking = [
            RankingEntry("anime.yaml", "First", "S", "ANIME", (1,)),
            RankingEntry("anime.yaml", "Second", "S", "ANIME", (1,)),
        ]
        collections = {"ANIME": {1: media_entry(1, 8)}, "MANGA": {}}

        self.assertEqual(validate(ranking, collections), [])

    def test_validate_rejects_pending_and_ranked_duplicate(self):
        ranking = [
            RankingEntry("anime.yaml", "Ranked", "S", "ANIME", (1,)),
            RankingEntry("anilist-pending.yaml", "Pending", None, None, (1,)),
        ]
        collections = {"ANIME": {1: media_entry(1, 8)}, "MANGA": {}}

        errors = validate(ranking, collections)

        self.assertTrue(any("both pending and ranked" in error for error in errors))

    def test_load_allows_rows_without_anilist_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            yaml_dir = Path(directory)
            for filename in (
                "anime.yaml",
                "manga-completed.yaml",
                "manga-ongoing.yaml",
                "novel.yaml",
            ):
                content = "- title: Example\n  tier: S\n"
                if filename != "anime.yaml":
                    content = "[]\n"
                (yaml_dir / filename).write_text(content, encoding="utf-8")

            _, errors = load_ranking_entries(yaml_dir)

        self.assertEqual(errors, [])

    def test_tierless_optional_file_can_cover_anilist_media(self):
        ranking = [RankingEntry("star-wars.yaml", "Visions", None, None, (1,))]
        collections = {"ANIME": {1: media_entry(1, 7)}, "MANGA": {}}

        self.assertEqual(validate(ranking, collections), [])

    def test_per_id_score_override_allows_grouped_media(self):
        ranking = [
            RankingEntry("anime.yaml", "Series", "SS", "ANIME", (1, 2), ((2, 8),))
        ]
        collections = {
            "ANIME": {1: media_entry(1, 9), 2: media_entry(2, 8)},
            "MANGA": {},
        }

        self.assertEqual(validate(ranking, collections), [])

    def test_reverse_check_ignores_non_completed_anime(self):
        current = media_entry(1, 8)
        current["status"] = "CURRENT"

        self.assertEqual(validate([], {"ANIME": {1: current}, "MANGA": {}}), [])

    def test_reverse_check_still_includes_current_manga(self):
        current = media_entry(1, 8, media_type="MANGA", media_format="MANGA")
        current["status"] = "CURRENT"

        errors = validate([], {"ANIME": {}, "MANGA": {1: current}})

        self.assertTrue(any("no story-ranking mapping" in error for error in errors))


if __name__ == "__main__":
    unittest.main()

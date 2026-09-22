from types import SimpleNamespace

import pytest
import yaml
from ruamel.yaml import YAML

from scripts import backfill_native_titles_from_wikidata as wikidata
from scripts import backfill_story_ranking_native_titles as anilist


@pytest.mark.parametrize(
    ("module", "fetch_name", "identifier"),
    [
        pytest.param(anilist, "fetch_native_titles", 20954, id="anilist"),
        pytest.param(
            wikidata, "fetch_japanese_titles", "a-silent-voice", id="wikidata"
        ),
    ],
)
@pytest.mark.parametrize(
    "translations",
    [
        pytest.param(None, id="no-block"),
        pytest.param({"en": {"title": "A Silent Voice"}}, id="other-language"),
        pytest.param({"ja": {"note": "備註"}}, id="japanese-sibling"),
        pytest.param(
            {"en": {"title": "A Silent Voice"}, "ja": {"note": "備註"}}, id="both"
        ),
        pytest.param({"ja": {"title": ""}}, id="explicit-empty"),
        pytest.param({"ja": {"title": "既存のタイトル"}}, id="existing-title"),
    ],
)
def test_backfill_merges_translations_and_preserves_existing_titles(
    tmp_path, monkeypatch, module, fetch_name, identifier, translations
):
    path = tmp_path / "anime.yaml"
    source = "# Tier SSS\n- title: '聲之形'  # keep this comment\n  external_ids:\n    anilist: [20954]\n    letterboxd: [a-silent-voice]\n"
    if translations is not None:
        source += "".join(
            "  " + line + "\n"
            for line in yaml.safe_dump(
                {"translations": translations}, allow_unicode=True
            ).splitlines()
        )
    source += "- title: 'Untouched'\n  reviews: []\n"
    path.write_text(source, encoding="utf-8")
    expected = yaml.safe_load(source)
    japanese = expected[0].setdefault("translations", {}).setdefault("ja", {})
    missing = "title" not in japanese
    japanese.setdefault("title", "聲の形 '特別版'")
    requested = []

    def fetch(identifiers):
        requested.append(identifiers)
        return {identifier: "聲の形 '特別版'"}

    monkeypatch.setattr(module, "RANKING_DIR", tmp_path)
    monkeypatch.setattr(
        module, "parse_args", lambda: SimpleNamespace(apply=True, limit=15)
    )
    monkeypatch.setattr(module, fetch_name, fetch)
    assert module.main() == 0
    # The strict loader rejects duplicate keys instead of silently taking the last.
    assert YAML(typ="safe").load(path.read_text()) == expected
    assert "# Tier SSS" in path.read_text()
    assert "'聲之形'  # keep this comment" in path.read_text()
    assert "'Untouched'" in path.read_text()
    first_write = path.read_bytes()
    assert module.main() == 0
    assert path.read_bytes() == first_write
    assert requested == ([[identifier]] if missing else [])


@pytest.mark.parametrize("module", [anilist, wikidata], ids=["anilist", "wikidata"])
def test_backfill_stale_plan_does_not_overwrite_translation(tmp_path, module):
    path = tmp_path / "anime.yaml"
    original = "- title: 聲之形\n  translations:\n    ja:\n      title: ''\n"
    path.write_text(original, encoding="utf-8")
    if module is anilist:
        assert module.apply_to_file(path, [(0, "聲之形", "聲の形")]) == 0
    else:
        module.apply_to_file(path, {0: "聲の形"})
    assert path.read_text() == original

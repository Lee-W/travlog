import datetime
import sys

import pytest

from scripts.prepare_publication import (
    check,
    draft_status,
    main,
    prepare_post,
    publication_date,
)


def write_post(path, status="Status: draft"):
    header = [
        "Title: Example",
        "Date: 2026-01-01 12:00 +0800",
        "Category: Review",
        "Tags: Example",
        "Slug: example",
        "Authors: Wei Lee",
    ]
    if status:
        header.append(status)
    path.write_text("\n".join([*header, "", "Body", ""]), encoding="utf-8")


@pytest.fixture
def post_path(tmp_path):
    return tmp_path / "post.md"


def test_prepare_post_removes_draft_and_updates_date(post_path):
    write_post(post_path)

    changed = prepare_post(post_path, "2026-06-30 18:20 +0800")

    assert changed
    content = post_path.read_text(encoding="utf-8")
    assert "Date: 2026-06-30 18:20 +0800" in content
    assert "Status:" not in content
    assert content.endswith("\n")


def test_prepare_post_updates_date_when_status_already_removed(post_path):
    write_post(post_path, status="")

    changed = prepare_post(post_path, "2026-06-30 18:20 +0800")

    assert changed
    content = post_path.read_text(encoding="utf-8")
    assert "Date: 2026-06-30 18:20 +0800" in content
    assert "Status:" not in content


def test_prepare_post_is_idempotent_with_same_date(post_path):
    write_post(post_path)
    prepare_post(post_path, "2026-06-30 18:20 +0800")

    assert not prepare_post(post_path, "2026-06-30 18:20 +0800")


def test_prepare_post_refreshes_date_after_preparation(post_path):
    write_post(post_path)
    prepare_post(post_path, "2026-06-30 18:20 +0800")

    assert prepare_post(post_path, "2026-06-30 18:21 +0800")
    assert "Date: 2026-06-30 18:21 +0800" in post_path.read_text(encoding="utf-8")


def test_check_rejects_changed_draft(post_path):
    write_post(post_path)

    assert check([post_path]) == 1
    assert draft_status(post_path)


def test_prepare_mode_is_noop_when_no_posts_changed(monkeypatch):
    argv = ["prepare_publication.py", "prepare", "--base-ref", "origin/main"]
    monkeypatch.setattr(sys, "argv", argv)
    monkeypatch.setattr("scripts.prepare_publication.changed_posts", lambda base_ref: [])

    assert main() == 0


def test_check_mode_fails_when_no_posts_changed(monkeypatch):
    argv = ["prepare_publication.py", "check", "--base-ref", "origin/main"]
    monkeypatch.setattr(sys, "argv", argv)
    monkeypatch.setattr("scripts.prepare_publication.changed_posts", lambda base_ref: [])

    assert main() == 1


def test_publication_date_uses_taiwan_timezone():
    utc = datetime.datetime(2026, 6, 30, 10, 20, tzinfo=datetime.UTC)

    assert publication_date(utc) == "2026-06-30 18:20 +0800"

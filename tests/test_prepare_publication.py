import datetime
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.prepare_publication import (
    changed_posts,
    check,
    check_filename_numbers,
    check_filename_references,
    draft_status,
    has_publish_commit,
    main,
    prepare,
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
    return tmp_path / "01-post.md"


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


def test_filename_number_uses_latest_published_post_and_ignores_drafts(tmp_path):
    published = tmp_path / "01-published.md"
    reserved_by_draft = tmp_path / "02-other-draft.md"
    publishing = tmp_path / "02-publishing.md"
    write_post(published, status="")
    write_post(reserved_by_draft)
    write_post(publishing)

    assert check_filename_numbers([publishing]) == 0


def test_filename_number_rejects_number_after_an_unpublished_draft(tmp_path):
    published = tmp_path / "01-published.md"
    draft = tmp_path / "02-other-draft.md"
    publishing = tmp_path / "03-publishing.md"
    write_post(published, status="")
    write_post(draft)
    write_post(publishing)

    assert check_filename_numbers([publishing]) == 1


def test_prepare_corrects_filename_before_changing_metadata(tmp_path):
    published = tmp_path / "01-published.md"
    publishing = tmp_path / "03-publishing.md"
    write_post(published, status="")
    write_post(publishing)

    assert prepare([publishing], "2026-06-30 18:20 +0800") == 0
    corrected = tmp_path / "02-publishing.md"
    assert corrected.exists()
    assert not publishing.exists()
    content = corrected.read_text(encoding="utf-8")
    assert "Date: 2026-06-30 18:20 +0800" in content
    assert "Status:" not in content


def test_prepare_moves_colliding_draft_after_publishing_post(tmp_path):
    published = tmp_path / "01-published.md"
    other_draft = tmp_path / "02-other-draft.md"
    publishing = tmp_path / "03-publishing.md"
    write_post(published, status="")
    write_post(other_draft)
    write_post(publishing)

    assert prepare([publishing], "2026-06-30 18:20 +0800") == 0
    assert (tmp_path / "02-publishing.md").exists()
    moved_draft = tmp_path / "03-other-draft.md"
    assert moved_draft.exists()
    assert draft_status(moved_draft)


def test_prepare_updates_references_to_renamed_posts(tmp_path):
    content = tmp_path / "content"
    posts = content / "posts" / "review" / "2026"
    places = content / "places"
    posts.mkdir(parents=True)
    places.mkdir()
    published = posts / "01-published.md"
    publishing = posts / "new-post.md"
    write_post(published, status="")
    write_post(publishing)
    place = places / "restaurant.yaml"
    place.write_text(
        'href: "{filename}/posts/review/2026/new-post.md#menu"\n',
        encoding="utf-8",
    )

    assert prepare([publishing], "2026-06-30 18:20 +0800") == 0
    assert place.read_text(encoding="utf-8") == (
        'href: "{filename}/posts/review/2026/02-new-post.md#menu"\n'
    )


def test_prepare_repairs_stale_unnumbered_reference(tmp_path):
    content = tmp_path / "content"
    posts = content / "posts" / "review" / "2026"
    places = content / "places"
    posts.mkdir(parents=True)
    places.mkdir()
    published = posts / "01-yodo-ramen.md"
    publishing = posts / "02-another-round.md"
    write_post(published, status="")
    write_post(publishing)
    place = places / "restaurant.yaml"
    place.write_text(
        'href: "{filename}/posts/review/2026/yodo-ramen.md"\n',
        encoding="utf-8",
    )

    assert prepare([publishing], "2026-06-30 18:20 +0800") == 0
    assert place.read_text(encoding="utf-8") == (
        'href: "{filename}/posts/review/2026/01-yodo-ramen.md"\n'
    )


def test_prepare_does_not_guess_ambiguous_unnumbered_reference(tmp_path):
    content = tmp_path / "content"
    posts = content / "posts" / "review" / "2026"
    places = content / "places"
    posts.mkdir(parents=True)
    places.mkdir()
    first = posts / "01-example.md"
    second = posts / "02-example.md"
    publishing = posts / "03-publishing.md"
    write_post(first, status="")
    write_post(second, status="")
    write_post(publishing)
    place = places / "restaurant.yaml"
    original = 'href: "{filename}/posts/review/2026/example.md"\n'
    place.write_text(original, encoding="utf-8")

    assert prepare([publishing], "2026-06-30 18:20 +0800") == 1
    assert place.read_text(encoding="utf-8") == original


def test_check_rejects_reference_to_missing_post(tmp_path):
    content = tmp_path / "content"
    posts = content / "posts" / "review" / "2026"
    pages = content / "pages"
    posts.mkdir(parents=True)
    pages.mkdir()
    publishing = posts / "01-publishing.md"
    write_post(publishing, status="")
    (pages / "index.md").write_text(
        "[Missing]({filename}/posts/review/2026/02-missing.md)\n",
        encoding="utf-8",
    )

    assert check_filename_references([publishing]) == 1


def test_check_accepts_reference_with_anchor(tmp_path):
    content = tmp_path / "content"
    posts = content / "posts" / "review" / "2026"
    pages = content / "pages"
    posts.mkdir(parents=True)
    pages.mkdir()
    publishing = posts / "01-publishing.md"
    write_post(publishing, status="")
    (pages / "index.md").write_text(
        "[Existing]({filename}/posts/review/2026/01-publishing.md#section.md)\n",
        encoding="utf-8",
    )

    assert check_filename_references([publishing]) == 0


def test_filename_number_requires_zero_padding(tmp_path):
    publishing = tmp_path / "1-publishing.md"
    write_post(publishing)

    assert check_filename_numbers([publishing]) == 1


def test_filename_numbers_accept_consecutive_posts_published_together(tmp_path):
    published = tmp_path / "01-published.md"
    first = tmp_path / "02-first.md"
    second = tmp_path / "03-second.md"
    write_post(published, status="")
    write_post(first)
    write_post(second)

    assert check_filename_numbers([second, first]) == 0


def test_prepare_mode_fails_when_no_posts_changed(monkeypatch):
    argv = ["prepare_publication.py", "prepare", "--base-ref", "origin/main"]
    monkeypatch.setattr(sys, "argv", argv)
    monkeypatch.setattr(
        "scripts.prepare_publication.has_publish_commit", lambda base_ref: True
    )
    monkeypatch.setattr("scripts.prepare_publication.changed_posts", lambda base_ref: [])

    assert main() == 1


def test_check_mode_fails_when_no_posts_changed(monkeypatch):
    argv = ["prepare_publication.py", "check", "--base-ref", "origin/main"]
    monkeypatch.setattr(sys, "argv", argv)
    monkeypatch.setattr(
        "scripts.prepare_publication.has_publish_commit", lambda base_ref: True
    )
    monkeypatch.setattr("scripts.prepare_publication.changed_posts", lambda base_ref: [])

    assert main() == 1


def test_main_is_noop_without_publish_commit(monkeypatch):
    argv = ["prepare_publication.py", "check", "--base-ref", "origin/main"]
    monkeypatch.setattr(sys, "argv", argv)
    monkeypatch.setattr(
        "scripts.prepare_publication.has_publish_commit", lambda base_ref: False
    )

    assert main() == 0


def test_check_mode_requires_preparation_commit(monkeypatch, post_path):
    write_post(post_path, status="")
    monkeypatch.setattr(
        sys,
        "argv",
        ["prepare_publication.py", "check", "--base-ref", "origin/main"],
    )
    monkeypatch.setattr(
        "scripts.prepare_publication.has_publish_commit", lambda base_ref: True
    )
    monkeypatch.setattr(
        "scripts.prepare_publication.changed_posts", lambda base_ref: [post_path]
    )
    monkeypatch.setattr("scripts.prepare_publication.head_is_prepared", lambda: False)

    assert main() == 1


def test_check_mode_accepts_prepared_branch_tip(monkeypatch, post_path):
    write_post(post_path, status="")
    monkeypatch.setattr(
        sys,
        "argv",
        ["prepare_publication.py", "check", "--base-ref", "origin/main"],
    )
    monkeypatch.setattr(
        "scripts.prepare_publication.has_publish_commit", lambda base_ref: True
    )
    monkeypatch.setattr(
        "scripts.prepare_publication.changed_posts", lambda base_ref: [post_path]
    )
    monkeypatch.setattr("scripts.prepare_publication.head_is_prepared", lambda: True)

    assert main() == 0


def test_check_mode_ignores_draft_renamed_to_resolve_collision(monkeypatch, tmp_path):
    publishing = tmp_path / "01-publishing.md"
    moved_draft = tmp_path / "02-other-draft.md"
    write_post(publishing, status="")
    write_post(moved_draft)
    monkeypatch.setattr(
        sys,
        "argv",
        ["prepare_publication.py", "check", "--base-ref", "origin/main"],
    )
    monkeypatch.setattr(
        "scripts.prepare_publication.has_publish_commit", lambda base_ref: True
    )
    monkeypatch.setattr(
        "scripts.prepare_publication.changed_posts",
        lambda base_ref: [publishing, moved_draft],
    )
    monkeypatch.setattr("scripts.prepare_publication.head_is_prepared", lambda: True)

    assert main() == 0


def test_changed_posts_includes_renamed_draft_but_not_published_post(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    subprocess.run(["git", "init", "-q"], check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], check=True)
    subprocess.run(["git", "config", "user.name", "Test"], check=True)
    posts = tmp_path / "content" / "posts"
    posts.mkdir(parents=True)
    draft = posts / "01-draft.md"
    published = posts / "02-published.md"
    write_post(draft)
    write_post(published, status="")
    subprocess.run(["git", "add", "content/posts"], check=True)
    subprocess.run(["git", "commit", "-q", "-m", "config: base"], check=True)
    subprocess.run(["git", "branch", "base"], check=True)

    renamed_draft = posts / "02-draft.md"
    renamed_published = posts / "01-published.md"
    subprocess.run(["git", "mv", draft, renamed_draft], check=True)
    subprocess.run(["git", "mv", published, renamed_published], check=True)
    renamed_draft.write_text(
        renamed_draft.read_text(encoding="utf-8").replace("Status: draft\n", ""),
        encoding="utf-8",
    )
    subprocess.run(["git", "commit", "-q", "-am", "new post: example"], check=True)

    assert changed_posts("base") == [
        Path("content/posts/02-draft.md"),
    ]


def test_has_publish_commit_detects_prefixed_subject(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    subprocess.run(["git", "init", "-q"], check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], check=True)
    subprocess.run(["git", "config", "user.name", "Test"], check=True)
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    subprocess.run(["git", "add", "a.txt"], check=True)
    subprocess.run(["git", "commit", "-q", "-m", "config: base"], check=True)
    subprocess.run(["git", "branch", "base"], check=True)

    (tmp_path / "b.txt").write_text("b", encoding="utf-8")
    subprocess.run(["git", "add", "b.txt"], check=True)
    subprocess.run(["git", "commit", "-q", "-m", "new draft: example"], check=True)

    assert has_publish_commit("base") is False

    (tmp_path / "c.txt").write_text("c", encoding="utf-8")
    subprocess.run(["git", "add", "c.txt"], check=True)
    subprocess.run(["git", "commit", "-q", "-m", "new post: example"], check=True)

    assert has_publish_commit("base") is True


def test_publication_date_uses_taiwan_timezone():
    utc = datetime.datetime(2026, 6, 30, 10, 20, tzinfo=datetime.UTC)

    assert publication_date(utc) == "2026-06-30 18:20 +0800"

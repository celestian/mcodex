from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from mcodex.cli_utils import locate_text_dir_for_build


def _write_repo_config(repo_root: Path) -> None:
    cfg = repo_root / ".mcodex" / "config.yaml"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text("{}\n", encoding="utf-8")


def _write_text_dir(text_dir: Path, *, slug: str) -> None:
    text_dir.mkdir(parents=True, exist_ok=True)
    (text_dir / "text.md").write_text("hello", encoding="utf-8")
    (text_dir / "metadata.yaml").write_text(
        yaml.safe_dump(
            {
                "metadata_version": 1,
                "id": "x",
                "title": "T",
                "slug": slug,
                "created_at": "2026-01-03T00:00:00+01:00",
                "authors": [],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )


def test_build_resolution_one_arg_in_text_dir_is_ref(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "repo"
    _write_repo_config(repo)
    text_dir = repo / "text_story"
    _write_text_dir(text_dir, slug="story")

    monkeypatch.chdir(text_dir)
    resolved_dir, resolved_ref = locate_text_dir_for_build(text="draft-1", ref=None)

    assert resolved_dir == text_dir
    assert resolved_ref == "draft-1"


def test_build_resolution_one_arg_in_repo_root_is_text(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "repo"
    _write_repo_config(repo)
    text_dir = repo / "text_story"
    _write_text_dir(text_dir, slug="story")

    monkeypatch.chdir(repo)
    resolved_dir, resolved_ref = locate_text_dir_for_build(text="story", ref=None)

    assert resolved_dir == text_dir
    assert resolved_ref == "."


def test_build_resolution_two_args_is_text_ref(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "repo"
    _write_repo_config(repo)
    text_dir = repo / "text_story"
    _write_text_dir(text_dir, slug="story")

    monkeypatch.chdir(repo)
    resolved_dir, resolved_ref = locate_text_dir_for_build(
        text="story",
        ref="draft-1",
    )

    assert resolved_dir == text_dir
    assert resolved_ref == "draft-1"


def test_build_resolution_outside_repo_requires_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir(parents=True)

    text_dir = tmp_path / "text_dir"
    _write_text_dir(text_dir, slug="story")

    monkeypatch.chdir(outside)

    with pytest.raises(FileNotFoundError, match="must be a path"):
        locate_text_dir_for_build(text="story", ref=None)

    resolved_dir, resolved_ref = locate_text_dir_for_build(
        text=str(text_dir),
        ref=".",
    )
    assert resolved_dir == text_dir
    assert resolved_ref == "."

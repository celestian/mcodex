from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from mcodex.cli_utils import resolve_text_dir


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


def test_status_resolve_text_dir_from_slug_inside_repo(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "repo"
    _write_repo_config(repo)

    text_dir = repo / "text_story"
    _write_text_dir(text_dir, slug="story")

    monkeypatch.chdir(repo)
    resolved = resolve_text_dir("story")
    assert resolved == text_dir


def test_status_resolve_text_dir_requires_path_outside_repo(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir(parents=True)

    monkeypatch.chdir(outside)
    with pytest.raises(FileNotFoundError, match="must be a path"):
        resolve_text_dir("story")


def test_status_resolve_text_dir_uses_cwd_when_none(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    text_dir = tmp_path / "text_story"
    _write_text_dir(text_dir, slug="story")

    monkeypatch.chdir(text_dir)
    resolved = resolve_text_dir(None)
    assert resolved == text_dir

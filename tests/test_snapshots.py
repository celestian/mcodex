from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import yaml

from mcodex.services.snapshot import snapshot_create


def _git_init(repo: Path) -> None:
    subprocess.run(["git", "-C", str(repo), "init"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.email", "test@example.com"],
        check=True,
    )
    (repo / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", ".gitignore"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-m", "init"], check=True)


def _write_min_text_dir(text_dir: Path) -> None:
    text_dir.mkdir(parents=True, exist_ok=True)
    (text_dir / "text.md").write_text("hello", encoding="utf-8")
    (text_dir / "metadata.yaml").write_text(
        yaml.safe_dump(
            {
                "metadata_version": 1,
                "id": "x",
                "title": "T",
                "slug": "t",
                "created_at": "2026-01-03T00:00:00+01:00",
                "authors": [],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )


def test_snapshot_create_commits_and_tags(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git_init(repo)

    tdir = repo / "text"
    _write_min_text_dir(tdir)

    snap = snapshot_create(text_dir=tdir, stage="draft", note="first")

    assert snap.exists()
    assert (snap / "snapshot.yaml").exists()

    data = yaml.safe_load((snap / "snapshot.yaml").read_text(encoding="utf-8"))
    assert data["label"] == "draft-1"
    assert data["git"]["tag"] == "mcodex/t/draft-1"

    tag_list = subprocess.run(
        ["git", "-C", str(repo), "tag", "-l", "mcodex/t/draft-1"],
        text=True,
        capture_output=True,
        check=True,
    )
    assert tag_list.stdout.strip() == "mcodex/t/draft-1"


def test_snapshot_disallows_going_backwards(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git_init(repo)

    tdir = repo / "text"
    _write_min_text_dir(tdir)

    snapshot_create(text_dir=tdir, stage="rc", note=None)

    with pytest.raises(ValueError, match="no longer allowed"):
        snapshot_create(text_dir=tdir, stage="draft", note=None)

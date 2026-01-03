from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from mcodex.services.snapshot import snapshot_create


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


def test_snapshot_create_copies_directory(tmp_path: Path) -> None:
    tdir = tmp_path / "text"
    _write_min_text_dir(tdir)
    (tdir / "outline.md").write_text("outline", encoding="utf-8")
    (tdir / "checklist.md").write_text("check", encoding="utf-8")

    snap = snapshot_create(text_dir=tdir, stage="draft", note=None)

    assert snap.exists()
    assert (snap / "text.md").read_text(encoding="utf-8") == "hello"
    assert (snap / "outline.md").read_text(encoding="utf-8") == "outline"
    assert (snap / "checklist.md").read_text(encoding="utf-8") == "check"
    assert (snap / "snapshot.yaml").exists()


def test_snapshot_autonumbers_per_stage(tmp_path: Path) -> None:
    tdir = tmp_path / "text"
    _write_min_text_dir(tdir)

    s1 = snapshot_create(text_dir=tdir, stage="draft", note=None)
    s2 = snapshot_create(text_dir=tdir, stage="draft", note=None)

    assert s1.name == "draft-1"
    assert s2.name == "draft-2"


def test_snapshot_disallows_going_backwards(tmp_path: Path) -> None:
    tdir = tmp_path / "text"
    _write_min_text_dir(tdir)

    snapshot_create(text_dir=tdir, stage="rc", note=None)

    with pytest.raises(ValueError, match="no longer allowed"):
        snapshot_create(text_dir=tdir, stage="draft", note=None)

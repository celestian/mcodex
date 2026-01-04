from __future__ import annotations

from pathlib import Path

from mcodex.services.snapshot import normalize_snapshot_label


def _mk_snapshot(text_dir: Path, name: str) -> None:
    p = text_dir / ".snapshot" / name
    p.mkdir(parents=True, exist_ok=True)


def test_normalize_stage_to_next_number(tmp_path: Path) -> None:
    text_dir = tmp_path / "text"
    text_dir.mkdir(parents=True, exist_ok=True)

    assert (
        normalize_snapshot_label(text_dir=text_dir, label_or_stage="draft") == "draft-1"
    )

    _mk_snapshot(text_dir, "draft-1")
    _mk_snapshot(text_dir, "draft-2")

    assert (
        normalize_snapshot_label(text_dir=text_dir, label_or_stage="draft") == "draft-3"
    )


def test_normalize_keeps_explicit_label(tmp_path: Path) -> None:
    text_dir = tmp_path / "text"
    text_dir.mkdir(parents=True, exist_ok=True)

    assert (
        normalize_snapshot_label(text_dir=text_dir, label_or_stage="draft-7")
        == "draft-7"
    )

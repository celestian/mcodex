from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

_STAGES: list[str] = ["draft", "preview", "rc", "final", "published"]
_STAGE_INDEX: dict[str, int] = {s: i for i, s in enumerate(_STAGES)}
_SNAP_RE = re.compile(r"^(draft|preview|rc|final|published)-(\d+)$")


def _snapshot_root(text_dir: Path) -> Path:
    return text_dir.expanduser().resolve() / ".snapshot"


def _validate_stage(stage: str) -> str:
    s = stage.strip()
    if s not in _STAGE_INDEX:
        allowed = ", ".join(_STAGES)
        raise ValueError(f"Unknown stage: {s}. Allowed: {allowed}")
    return s


def _list_snapshot_dirs(text_dir: Path) -> list[Path]:
    root = _snapshot_root(text_dir)
    if not root.exists():
        return []
    return [p for p in root.iterdir() if p.is_dir() and _SNAP_RE.match(p.name)]


def _highest_stage_index(text_dir: Path) -> int | None:
    highest: int | None = None
    for p in _list_snapshot_dirs(text_dir):
        m = _SNAP_RE.match(p.name)
        if not m:
            continue
        stage = m.group(1)
        idx = _STAGE_INDEX[stage]
        if highest is None or idx > highest:
            highest = idx
    return highest


def _next_number(text_dir: Path, stage: str) -> int:
    root = _snapshot_root(text_dir)
    if not root.exists():
        return 1

    mx = 0
    prefix = f"{stage}-"
    for p in root.iterdir():
        if not p.is_dir():
            continue
        name = p.name
        if not name.startswith(prefix):
            continue
        m = _SNAP_RE.match(name)
        if not m:
            continue
        n = int(m.group(2))
        mx = max(mx, n)
    return mx + 1


def _ignore_for_copy(_: str, names: list[str]) -> set[str]:
    ignore = {".snapshot", ".git", "__pycache__"}
    ignore.update({"build", "exports"})
    return {n for n in names if n in ignore}


def _write_snapshot_info(snapshot_dir: Path, data: dict[str, Any]) -> None:
    p = snapshot_dir / "snapshot.yaml"
    p.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def snapshot_create(*, text_dir: Path, stage: str, note: str | None) -> Path:
    tdir = text_dir.expanduser().resolve()
    if not tdir.exists():
        raise FileNotFoundError(f"Text directory does not exist: {tdir}")
    if not tdir.is_dir():
        raise NotADirectoryError(f"Text path is not a directory: {tdir}")

    st = _validate_stage(stage)
    highest = _highest_stage_index(tdir)
    target_idx = _STAGE_INDEX[st]

    if highest is not None and target_idx < highest:
        allowed = ", ".join(_STAGES[highest:])
        raise ValueError(
            f"Stage '{st}' is no longer allowed for this text. "
            f"Available stages: {allowed}"
        )

    n = _next_number(tdir, st)
    label = f"{st}-{n}"

    root = _snapshot_root(tdir)
    root.mkdir(parents=True, exist_ok=True)

    snapshot_dir = root / label
    if snapshot_dir.exists():
        raise FileExistsError(f"Snapshot already exists: {snapshot_dir}")

    shutil.copytree(
        tdir,
        snapshot_dir,
        ignore=_ignore_for_copy,
        dirs_exist_ok=False,
    )

    info = {
        "label": label,
        "stage": st,
        "number": n,
        "created_at": datetime.now().astimezone().isoformat(),
        "note": (note.strip() if note and note.strip() else None),
    }
    _write_snapshot_info(snapshot_dir, info)

    return snapshot_dir


def snapshot_list(*, text_dir: Path) -> None:
    tdir = text_dir.expanduser().resolve()
    root = _snapshot_root(tdir)
    if not root.exists():
        print("No snapshots found.")
        return

    def _sort_key(p: Path) -> tuple[int, str]:
        m = _SNAP_RE.match(p.name)
        assert m is not None
        stage = m.group(1)
        return _STAGE_INDEX[stage], p.name

    snaps = sorted(
        (p for p in root.iterdir() if p.is_dir() and _SNAP_RE.match(p.name)),
        key=_sort_key,
    )
    if not snaps:
        print("No snapshots found.")
        return

    for p in snaps:
        print(p.name)


def available_stages(*, text_dir: Path) -> list[str]:
    tdir = text_dir.expanduser().resolve()
    highest = _highest_stage_index(tdir)
    if highest is None:
        return _STAGES[:]
    return _STAGES[highest:]


def current_stage(*, text_dir: Path) -> str | None:
    tdir = text_dir.expanduser().resolve()
    highest = _highest_stage_index(tdir)
    if highest is None:
        return None
    return _STAGES[highest]

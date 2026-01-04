from __future__ import annotations

import re
import shutil
import subprocess
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from mcodex.config import get_snapshot_commit_template
from mcodex.metadata import load_metadata

_STAGES: list[str] = ["draft", "preview", "rc", "final", "published"]
_STAGE_INDEX: dict[str, int] = {s: i for i, s in enumerate(_STAGES)}

_SNAP_RE = re.compile(r"^(?P<stage>[a-z]+)-(?P<num>[0-9]+)$")
_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


class GitRepoNotFoundError(RuntimeError):
    pass


def _run_git(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def _git_root_for(path: Path) -> Path:
    completed = _run_git(["rev-parse", "--show-toplevel"], cwd=path)
    if completed.returncode != 0:
        raise GitRepoNotFoundError("Git repository not found")
    return Path(completed.stdout.strip()).expanduser().resolve()


def _snapshot_root(text_dir: Path) -> Path:
    return text_dir / ".snapshot"


def _list_snapshot_dirs(text_dir: Path) -> list[Path]:
    root = _snapshot_root(text_dir)
    if not root.exists():
        return []
    return [p for p in root.iterdir() if p.is_dir() and p.name != ".gitkeep"]


def _highest_stage_index(text_dir: Path) -> int | None:
    highest: int | None = None
    for p in _list_snapshot_dirs(text_dir):
        m = _SNAP_RE.match(p.name)
        if not m:
            continue
        stage = m.group("stage")
        if stage not in _STAGE_INDEX:
            continue
        idx = _STAGE_INDEX[stage]
        if highest is None or idx > highest:
            highest = idx
    return highest


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


def _next_number_for_stage(text_dir: Path, stage: str) -> int:
    nums: list[int] = []
    for p in _list_snapshot_dirs(text_dir):
        m = _SNAP_RE.match(p.name)
        if not m:
            continue
        if m.group("stage") != stage:
            continue
        nums.append(int(m.group("num")))
    return (max(nums) + 1) if nums else 1


def _copy_text_dir(
    *,
    src: Path,
    dst: Path,
    ignore_names: Iterable[str],
) -> None:
    ignored = set(ignore_names)

    def _ignore(_: str, names: list[str]) -> set[str]:
        return {n for n in names if n in ignored}

    shutil.copytree(src, dst, ignore=_ignore, dirs_exist_ok=False)


def _write_snapshot_yaml(
    *,
    path: Path,
    label: str,
    note: str | None,
    git_tag: str,
    text_slug: str,
) -> None:
    payload: dict[str, Any] = {
        "label": label,
        "created_at": datetime.now().astimezone().isoformat(),
        "text": {"slug": text_slug},
        "git": {
            "tag": git_tag,
        },
    }
    if note:
        payload["note"] = note
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def _format_commit_message(
    *,
    repo_root: Path,
    slug: str,
    label: str,
    note: str | None,
) -> str:
    tpl = get_snapshot_commit_template(repo_root=repo_root)
    safe_note = note or ""
    return tpl.format(slug=slug, label=label, note=safe_note).strip()


def _extract_metadata_dict(result: Any) -> dict[str, Any]:
    if isinstance(result, dict):
        return result

    if isinstance(result, (tuple, list)) and result:
        head = result[0]
        if isinstance(head, dict):
            return head

    return {}


def snapshot_create(*, text_dir: Path, label: str, note: str | None) -> Path:
    tdir = text_dir.expanduser().resolve()
    safe_label = str(label).strip()
    if not safe_label:
        raise ValueError("Snapshot label must not be empty.")
    if not _LABEL_RE.match(safe_label):
        raise ValueError(
            "Invalid snapshot label. Allowed: letters, digits, '.', '_', '-' "
            "(must start with letter or digit)."
        )

    repo_root = _git_root_for(tdir)

    meta_path = tdir / "metadata.yaml"
    meta = _extract_metadata_dict(load_metadata(meta_path))
    slug = str(meta.get("slug") or tdir.name)

    root = _snapshot_root(tdir)
    root.mkdir(parents=True, exist_ok=True)

    snap_dir = root / safe_label
    if snap_dir.exists():
        raise FileExistsError(f"Snapshot already exists: {snap_dir}")

    tag = f"mcodex/{slug}/{safe_label}"

    # Copy the whole text directory into the snapshot directory.
    # Ignore snapshot root itself to avoid recursion.
    _copy_text_dir(src=tdir, dst=snap_dir, ignore_names=[root.name, ".git"])

    _write_snapshot_yaml(
        path=snap_dir / "snapshot.yaml",
        label=safe_label,
        note=note,
        git_tag=tag,
        text_slug=slug,
    )

    # Git commit + tag.
    rel_snap_dir = snap_dir.relative_to(repo_root)

    add_cp = _run_git(["add", str(rel_snap_dir)], cwd=repo_root)
    if add_cp.returncode != 0:
        raise RuntimeError(
            f"Git add failed:\nout: {add_cp.stdout}\nerr: {add_cp.stderr}\n"
        )

    msg = _format_commit_message(
        repo_root=repo_root,
        slug=slug,
        label=safe_label,
        note=note,
    )

    commit_cp = _run_git(["commit", "-m", msg], cwd=repo_root)
    if commit_cp.returncode != 0:
        raise RuntimeError(
            f"Git commit failed:\nout: {commit_cp.stdout}\nerr: {commit_cp.stderr}\n"
        )

    tag_cp = _run_git(["tag", tag], cwd=repo_root)
    if tag_cp.returncode != 0:
        raise RuntimeError(
            f"Git tag failed:\nout: {tag_cp.stdout}\nerr: {tag_cp.stderr}\n"
        )

    return snap_dir


def snapshot_list(*, text_dir: Path) -> None:
    tdir = text_dir.expanduser().resolve()
    items = sorted(_list_snapshot_dirs(tdir), key=lambda p: p.name)
    if not items:
        print("No snapshots found.")
        return
    for p in items:
        print(p.name)

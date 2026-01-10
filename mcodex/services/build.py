from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mcodex.config import (
    DEFAULT_ARTIFACTS_DIR,
    RepoConfigNotFoundError,
    find_repo_root,
    get_artifacts_dir,
)
from mcodex.constants import SNAPSHOT_LABEL_PATTERN
from mcodex.metadata import load_metadata
from mcodex.path_utils import get_metadata_path, normalize_path
from mcodex.services.pipeline import run_pipeline

_SNAP_RE = SNAPSHOT_LABEL_PATTERN


@dataclass(frozen=True)
class BuildSource:
    source_dir: Path
    version_label: str


def build(*, text_dir: Path, ref: str, pipeline: str = "pdf") -> Path:
    """Build a document artifact.

    Args:
        text_dir: Path to the text directory.
        ref: "." for worktree, a snapshot label (e.g. "draft-3"),
             or a stage name (e.g. "draft") which resolves to latest "draft-N".
        pipeline: Build pipeline name. Supported: "pdf", "noop".
    """

    pipeline_name = str(pipeline or "pdf").strip().lower()
    if pipeline_name == "noop":
        return _build_noop(text_dir=text_dir, version=ref)

    text_dir = normalize_path(text_dir)
    source = _resolve_source(text_dir=text_dir, version=ref)
    slug = _load_slug(source.source_dir)

    out_dir = _resolve_artifacts_dir(text_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    out_ext = _pipeline_output_ext(pipeline_name)
    out_name = f"{slug}_{source.version_label}.{out_ext}"
    out_path = out_dir / out_name

    run_pipeline(
        pipeline_name=pipeline_name,
        source_dir=source.source_dir,
        output_path=out_path,
        version_label=source.version_label,
    )
    return out_path


def build_pdf(*, text_dir: Path, version: str) -> Path:
    return build(text_dir=text_dir, ref=version, pipeline="pdf")


def _build_noop(*, text_dir: Path, version: str) -> Path:
    """A test-friendly pipeline that only resolves and writes a dummy file."""

    text_dir = text_dir.expanduser().resolve()
    source = _resolve_source(text_dir=text_dir, version=version)
    slug = _load_slug(source.source_dir)

    out_dir = _resolve_artifacts_dir(text_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    out_name = f"{slug}_{source.version_label}.pdf"
    out_path = out_dir / out_name

    out_path.write_text(
        f"noop build: {slug} / {source.version_label}\n",
        encoding="utf-8",
    )
    return out_path


def _resolve_artifacts_dir(text_dir: Path) -> Path:
    """Resolve the directory for build outputs.

    In a mcodex repo, outputs go to <repo_root>/<artifacts_dir>.
    Outside a repo, outputs go to <text_dir.parent>/artifacts.
    """

    try:
        repo_root = find_repo_root(text_dir)
    except RepoConfigNotFoundError:
        return text_dir.parent / DEFAULT_ARTIFACTS_DIR

    artifacts_dir = get_artifacts_dir(repo_root=repo_root)
    return repo_root / artifacts_dir


def _pipeline_output_ext(pipeline_name: str) -> str:
    if pipeline_name == "docx":
        return "docx"
    if pipeline_name == "latex":
        return "tex"
    if pipeline_name in {"pdf", "pdf_pandoc"}:
        return "pdf"
    return "pdf"


def _latest_snapshot_for_stage(text_dir: Path, stage: str) -> str | None:
    root = text_dir / ".snapshot"
    if not root.exists():
        return None

    best_num: int | None = None
    best_label: str | None = None

    for p in root.iterdir():
        if not p.is_dir() or p.name == ".gitkeep":
            continue
        m = _SNAP_RE.match(p.name)
        if not m:
            continue
        if m.group("stage") != stage:
            continue
        num = int(m.group("num"))
        if best_num is None or num > best_num:
            best_num = num
            best_label = p.name

    return best_label


def _resolve_source(*, text_dir: Path, version: str) -> BuildSource:
    label = str(version).strip() if version is not None else "."
    if label == ".":
        return BuildSource(source_dir=text_dir, version_label="worktree")

    snap_dir = text_dir / ".snapshot" / label
    if snap_dir.exists():
        if not snap_dir.is_dir():
            raise NotADirectoryError(f"Snapshot is not a directory: {snap_dir}")
        return BuildSource(source_dir=snap_dir, version_label=label)

    stage_candidate = label
    if stage_candidate.isalpha() and stage_candidate.islower():
        latest = _latest_snapshot_for_stage(text_dir, stage_candidate)
        if latest is not None:
            resolved = text_dir / ".snapshot" / latest
            return BuildSource(source_dir=resolved, version_label=latest)

    raise FileNotFoundError(f"Snapshot not found: {label}")


def _load_slug(source_dir: Path) -> str:
    meta = load_metadata(get_metadata_path(source_dir))
    slug = str(meta.get("slug") or "").strip()
    if slug:
        return slug
    return source_dir.name

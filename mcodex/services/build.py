from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from mcodex.config import (
    DEFAULT_ARTIFACTS_DIR,
    RepoConfigNotFoundError,
    find_repo_root,
    get_artifacts_dir,
)
from mcodex.metadata import load_metadata


@dataclass(frozen=True)
class BuildSource:
    source_dir: Path
    version_label: str


_LATEX_TEMPLATE = r"""\documentclass[12pt]{article}

\usepackage[a4paper,margin=25mm]{geometry}
\usepackage{fontspec}
\usepackage{microtype}
\usepackage{setspace}
\usepackage{parskip}
\usepackage{hyperref}

\providecommand{\tightlist}{}

\setstretch{1.15}

\begin{document}
\input{body.tex}
\end{document}
"""


def build(*, text_dir: Path, ref: str, pipeline: str = "pdf") -> Path:
    """Build a document artifact.

    Args:
        text_dir: Path to the text directory.
        ref: "." for worktree, otherwise a snapshot label.
        pipeline: Build pipeline name. Supported: "pdf", "noop".
    """

    pipeline_name = str(pipeline or "pdf").strip().lower()
    if pipeline_name == "pdf":
        return build_pdf(text_dir=text_dir, version=ref)
    if pipeline_name == "noop":
        return _build_noop(text_dir=text_dir, version=ref)

    raise ValueError(f"Unknown pipeline: {pipeline}")


def build_pdf(*, text_dir: Path, version: str) -> Path:
    text_dir = text_dir.expanduser().resolve()
    source = _resolve_source(text_dir=text_dir, version=version)
    slug = _load_slug(source.source_dir)

    out_dir = _resolve_artifacts_dir(text_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    out_name = f"{slug}_{source.version_label}.pdf"
    out_path = out_dir / out_name

    _build_pdf_pipeline(
        source_dir=source.source_dir,
        output_path=out_path,
    )
    return out_path


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


def _resolve_source(*, text_dir: Path, version: str) -> BuildSource:
    label = str(version).strip() if version is not None else "."
    if label == ".":
        return BuildSource(source_dir=text_dir, version_label="worktree")

    snap_dir = text_dir / ".snapshot" / label
    if not snap_dir.exists():
        raise FileNotFoundError(f"Snapshot not found: {label}")
    if not snap_dir.is_dir():
        raise NotADirectoryError(f"Snapshot is not a directory: {snap_dir}")

    return BuildSource(source_dir=snap_dir, version_label=label)


def _load_slug(source_dir: Path) -> str:
    meta = load_metadata(source_dir / "metadata.yaml")
    slug = str(meta.get("slug") or "").strip()
    if slug:
        return slug
    return source_dir.name


def _require_executable(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise RuntimeError(
            f"Required executable not found: {name}. "
            "Install it and ensure it is on PATH."
        )
    return path


def _build_pdf_pipeline(*, source_dir: Path, output_path: Path) -> None:
    pandoc = _require_executable("pandoc")
    vlna = _require_executable("vlna")
    latexmk = _require_executable("latexmk")

    src = source_dir / "text.md"
    if not src.exists():
        raise FileNotFoundError(f"Source text not found: {src}")

    with tempfile.TemporaryDirectory(prefix="mcodex-build-") as td:
        tmp = Path(td)
        body_raw = tmp / "body_raw.tex"
        body = tmp / "body.tex"
        main = tmp / "main.tex"

        _run(
            [
                pandoc,
                str(src),
                "--from=markdown",
                "--to=latex",
                "-o",
                str(body_raw),
            ],
            cwd=source_dir,
        )

        _run(
            [
                vlna,
                "-f",
                "-l",
                "-m",
                "-n",
                str(body_raw),
                str(body),
            ],
            cwd=tmp,
        )

        main.write_text(_LATEX_TEMPLATE, encoding="utf-8")

        # Force LuaLaTeX. latexmk internally calls the engine via the $pdflatex
        # command variable even when the engine is not pdfTeX.
        # This avoids surprises from latexmkrc defaults.
        try:
            _run(
                [
                    latexmk,
                    "-pdf",
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    "-file-line-error",
                    "-e",
                    "$pdflatex=q/lualatex %O %S/;",
                    str(main.name),
                ],
                cwd=tmp,
            )
        except RuntimeError as exc:
            log_path = tmp / "main.log"
            if log_path.exists():
                tail = _tail_text_file(log_path, max_chars=6000)
                raise RuntimeError(f"{exc}\n\n--- main.log (tail) ---\n{tail}") from exc
            raise

        built_pdf = tmp / "main.pdf"
        if not built_pdf.exists():
            raise RuntimeError("latexmk finished without producing main.pdf")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(built_pdf, output_path)


def _tail_text_file(path: Path, *, max_chars: int) -> str:
    data = path.read_text(encoding="utf-8", errors="replace")
    if len(data) <= max_chars:
        return data
    return data[-max_chars:]


def _run(cmd: list[str], *, cwd: Path) -> None:
    completed = subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        stdout = (completed.stdout or "").strip()
        stderr = (completed.stderr or "").strip()

        parts: list[str] = [f"Command failed: {' '.join(cmd)}"]
        if stdout:
            parts.append("--- stdout ---")
            parts.append(stdout)
        if stderr:
            parts.append("--- stderr ---")
            parts.append(stderr)
        if not stdout and not stderr:
            parts.append("(no output)")

        raise RuntimeError("\n".join(parts))

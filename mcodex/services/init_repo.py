from __future__ import annotations

import importlib.resources
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG: dict[str, Any] = {
    "artifacts_dir": "artifacts",
    "text_prefix": "text_",
    "git": {
        "commit_templates": {
            "snapshot": "Snapshot: {slug} / {label} — {note}",
        }
    },
    "pipelines": {
        # 1) md -> pandoc -> pdf
        "pdf_pandoc": {
            "steps": [
                {"kind": "pandoc", "from": "markdown", "to": "pdf"},
            ],
        },
        # 2) md -> pandoc -> docx
        "docx": {
            "steps": [
                {"kind": "pandoc", "from": "markdown", "to": "docx"},
            ],
        },
        # 3) md -> pandoc -> latex
        "latex": {
            "steps": [
                {
                    "kind": "pandoc",
                    "from": "markdown",
                    "to": "latex",
                },
            ],
        },
        # 4) md -> pandoc -> vlna -> latexmk(lualatex) -> pdf (default)
        "pdf": {
            "steps": [
                {
                    "kind": "pandoc",
                    "from": "markdown",
                    "to": "latex",
                    "output": "body_raw.tex",
                },
                {
                    "kind": "vlna",
                    "input": "body_raw.tex",
                    "output": "body.tex",
                },
                {
                    "kind": "latexmk",
                    "engine": "lualatex",
                    "main": "main.tex",
                },
            ],
        },
    },
}


def _write_default_config(path: Path) -> None:
    path.write_text(
        yaml.safe_dump(DEFAULT_CONFIG, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def _copy_tree(src_pkg: str, src_subdir: str, dst_dir: Path, *, force: bool) -> None:
    traversable = importlib.resources.files(src_pkg).joinpath(src_subdir)

    # Ensure we can use pathlib operations regardless of whether the package data
    # is on disk or in a zipped distribution.
    with importlib.resources.as_file(traversable) as src_root:
        src_root_path = Path(src_root)

        for item in src_root_path.rglob("*"):
            rel = item.relative_to(src_root_path)
            target = dst_dir / rel

            if item.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue

            if target.exists() and not force:
                continue

            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(item.read_bytes())


def _ensure_gitignore_contains(repo_root: Path, line: str) -> None:
    gi = repo_root / ".gitignore"
    existing = gi.read_text(encoding="utf-8").splitlines() if gi.exists() else []
    if line in existing:
        return
    content = "\n".join(existing) + ("\n" if existing else "") + line + "\n"
    gi.write_text(content, encoding="utf-8")


def init_repo(repo_root: Path, *, force: bool = False) -> None:
    """Initialize mcodex project structure in a repository.

    Creates:
    - .mcodex/config.yaml (if missing)
    - .mcodex/templates/ ... (copied from package defaults)
    Updates:
    - .gitignore to include artifacts/ (idempotent)
    """

    root = repo_root.expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"Repository root does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Repository root is not a directory: {root}")

    mcodex_dir = root / ".mcodex"
    mcodex_dir.mkdir(parents=True, exist_ok=True)

    cfg_path = mcodex_dir / "config.yaml"
    if not cfg_path.exists():
        _write_default_config(cfg_path)

    templates_dir = mcodex_dir / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)

    # Copy packaged templates into the repo (variant A).
    _copy_tree(
        "mcodex.package_templates",
        "templates",
        templates_dir,
        force=force,
    )

    _ensure_gitignore_contains(root, "artifacts/")

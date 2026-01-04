from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict
from pathlib import Path
from typing import Any

import yaml

from mcodex.models import Author


class RepoConfigNotFoundError(FileNotFoundError):
    """Raised when no `.mcodex/config.yaml` can be found by walking upwards."""


DEFAULT_SNAPSHOT_COMMIT_TEMPLATE = "Snapshot: {slug} / {label} — {note}"
DEFAULT_TEXT_PREFIX = "text_"


def repo_config_path(repo_root: Path) -> Path:
    return repo_root.expanduser().resolve() / ".mcodex" / "config.yaml"


def find_repo_root(start: Path | None = None) -> Path:
    """Find repo root by searching for `.mcodex/config.yaml` upwards.

    Args:
        start: Directory (or file within a directory) to start searching from.

    Raises:
        RepoConfigNotFoundError: if no repo config anchor is found.
    """

    p = (start or Path.cwd()).expanduser().resolve()
    if p.is_file():
        p = p.parent

    for candidate in [p, *p.parents]:
        if repo_config_path(candidate).exists():
            return candidate

    raise RepoConfigNotFoundError(
        "No .mcodex/config.yaml found. Run `mcodex init` in a Git repo first."
    )


def load_config(
    *,
    start: Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    root = repo_root or find_repo_root(start)
    cfg_path = repo_config_path(root)
    if not cfg_path.exists():
        return {}
    data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("Invalid config: root must be a mapping.")
    return data


def save_config(
    config: dict[str, Any],
    *,
    repo_root: Path | None = None,
    start: Path | None = None,
) -> None:
    root = repo_root or find_repo_root(start)
    cfg_path = repo_config_path(root)
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text(
        yaml.safe_dump(config, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def ensure_defaults(
    *,
    start: Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Ensure required defaults exist in repo config.

    This is intentionally conservative: it only ensures keys needed by existing
    functionality (authors + snapshot commit template).
    """

    cfg = load_config(start=start, repo_root=repo_root)

    git = cfg.get("git")
    if git is None or not isinstance(git, dict):
        git = {}
        cfg["git"] = git

    commit_templates = git.get("commit_templates")
    if commit_templates is None or not isinstance(commit_templates, dict):
        commit_templates = {}
        git["commit_templates"] = commit_templates

    if "snapshot" not in commit_templates:
        commit_templates["snapshot"] = DEFAULT_SNAPSHOT_COMMIT_TEMPLATE
        save_config(cfg, start=start, repo_root=repo_root)

    return cfg


def get_snapshot_commit_template(
    *,
    start: Path | None = None,
    repo_root: Path | None = None,
) -> str:
    cfg = ensure_defaults(start=start, repo_root=repo_root)
    git = cfg.get("git", {})
    commit_templates = git.get("commit_templates", {})
    tpl = commit_templates.get("snapshot")
    if not isinstance(tpl, str) or not tpl.strip():
        return DEFAULT_SNAPSHOT_COMMIT_TEMPLATE
    return tpl.strip()


def load_authors(
    *,
    start: Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, Author]:
    cfg = load_config(start=start, repo_root=repo_root)
    raw_authors = cfg.get("authors", [])
    out: dict[str, Author] = {}

    if not isinstance(raw_authors, list):
        return out

    for a in raw_authors:
        if not isinstance(a, dict):
            continue
        nickname = str(a.get("nickname", "")).strip()
        first_name = str(a.get("first_name", "")).strip()
        last_name = str(a.get("last_name", "")).strip()
        email = str(a.get("email", "")).strip()

        if not nickname or not first_name or not last_name or not email:
            continue

        out[nickname] = Author(
            nickname=nickname,
            first_name=first_name,
            last_name=last_name,
            email=email,
        )

    return out


def get_text_prefix(
    *,
    start: Path | None = None,
    repo_root: Path | None = None,
) -> str:
    cfg = load_config(start=start, repo_root=repo_root)
    raw = cfg.get("text_prefix")
    if not isinstance(raw, str):
        return DEFAULT_TEXT_PREFIX
    value = raw.strip()
    if not value:
        return DEFAULT_TEXT_PREFIX
    return value


def save_authors(
    authors: dict[str, Author],
    *,
    start: Path | None = None,
    repo_root: Path | None = None,
) -> None:
    cfg = load_config(start=start, repo_root=repo_root)
    cfg["authors"] = [asdict(a) for a in authors.values()]
    save_config(cfg, start=start, repo_root=repo_root)


def is_under_repo(start: Path | None = None) -> bool:
    try:
        find_repo_root(start)
    except RepoConfigNotFoundError:
        return False
    return True


def validate_allowed_roots(roots: Iterable[Path]) -> list[Path]:
    """Normalize allowed roots used in safety-critical operations."""

    out: list[Path] = []
    for r in roots:
        out.append(r.expanduser().resolve())
    return out

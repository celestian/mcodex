from __future__ import annotations

import os
from dataclasses import asdict
from pathlib import Path
from typing import Any

import yaml

from mcodex.models import Author

DEFAULT_SNAPSHOT_COMMIT_TEMPLATE = "Snapshot: {slug} / {label} — {note}"


def default_config_path() -> Path:
    override = os.environ.get("MCODEX_CONFIG_PATH")
    if override:
        return Path(override).expanduser().resolve()

    base = Path.home() / ".config" / "mcodex"
    return (base / "config.yaml").resolve()


def load_config(path: Path | None = None) -> dict[str, Any]:
    cfg_path = path or default_config_path()
    if not cfg_path.exists():
        return {}
    data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("Invalid config: root must be a mapping.")
    return data


def save_config(config: dict[str, Any], path: Path | None = None) -> None:
    cfg_path = path or default_config_path()
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text(
        yaml.safe_dump(config, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def ensure_git_defaults(path: Path | None = None) -> dict[str, Any]:
    cfg = load_config(path)

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
        save_config(cfg, path)

    return cfg


def get_snapshot_commit_template(path: Path | None = None) -> str:
    cfg = ensure_git_defaults(path)
    git = cfg.get("git", {})
    commit_templates = git.get("commit_templates", {})
    tpl = commit_templates.get("snapshot")
    if not isinstance(tpl, str) or not tpl.strip():
        return DEFAULT_SNAPSHOT_COMMIT_TEMPLATE
    return tpl.strip()


def load_authors(path: Path | None = None) -> dict[str, Author]:
    cfg = load_config(path)
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


def save_authors(authors: dict[str, Author], path: Path | None = None) -> None:
    cfg = load_config(path)
    cfg["authors"] = [asdict(a) for a in authors.values()]
    save_config(cfg, path)

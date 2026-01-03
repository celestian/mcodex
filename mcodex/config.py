from __future__ import annotations

import os
from dataclasses import asdict
from pathlib import Path

import yaml

from mcodex.models import Author


def default_config_path() -> Path:
    """
    Return the path to the user configuration file.

    If MCODEX_CONFIG_PATH is set, it is used as an override.
    Otherwise the default is ~/.config/mcodex/config.yaml.
    """
    override = os.environ.get("MCODEX_CONFIG_PATH")
    if override:
        return Path(override).expanduser()

    base = Path.home() / ".config" / "mcodex"
    return base / "config.yaml"


def load_authors(path: Path | None = None) -> dict[str, Author]:
    cfg_path = path or default_config_path()
    if not cfg_path.exists():
        return {}

    data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    raw_authors = data.get("authors", [])
    out: dict[str, Author] = {}

    for a in raw_authors:
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
    cfg_path = path or default_config_path()
    cfg_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "authors": [asdict(a) for a in authors.values()],
    }
    cfg_path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

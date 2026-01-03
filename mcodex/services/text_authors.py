from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import yaml

from mcodex.config import load_authors
from mcodex.models import Author


def _metadata_path(text_dir: Path) -> Path:
    return text_dir.expanduser().resolve() / "metadata.yaml"


def _load_metadata(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Metadata file not found: {path}")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _write_metadata(path: Path, data: dict) -> None:
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def _author_from_config(nickname: str) -> Author:
    authors = load_authors()
    if nickname not in authors:
        raise ValueError(f"Unknown author nickname: {nickname}")
    return authors[nickname]


def text_author_add(*, text_dir: Path, nickname: str) -> None:
    meta_path = _metadata_path(text_dir)
    data = _load_metadata(meta_path)

    author = _author_from_config(nickname)

    authors = data.get("authors")
    if authors is None:
        authors = []
        data["authors"] = authors

    if not isinstance(authors, list):
        raise ValueError("Invalid metadata: 'authors' must be a list.")

    if any(
        isinstance(a, dict) and a.get("nickname") == author.nickname for a in authors
    ):
        return

    authors.append(asdict(author))
    _write_metadata(meta_path, data)


def text_author_remove(*, text_dir: Path, nickname: str) -> None:
    meta_path = _metadata_path(text_dir)
    data = _load_metadata(meta_path)

    authors = data.get("authors")
    if authors is None:
        return
    if not isinstance(authors, list):
        raise ValueError("Invalid metadata: 'authors' must be a list.")

    kept: list[dict] = []
    removed = False
    for a in authors:
        if isinstance(a, dict) and a.get("nickname") == nickname:
            removed = True
            continue
        if isinstance(a, dict):
            kept.append(a)

    if not removed:
        return

    data["authors"] = kept
    _write_metadata(meta_path, data)

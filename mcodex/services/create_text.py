from __future__ import annotations

import re
import unicodedata
import uuid
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import yaml

from mcodex.config import load_authors
from mcodex.models import Author, TextMetadata

_SLUG_ALLOWED_RE = re.compile(r"[^a-z0-9_]+")


def normalize_title(title: str) -> str:
    raw = title.strip().lower()
    if not raw:
        raise ValueError("Title must not be empty.")

    no_diacritics = (
        unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode("ascii")
    )
    spaced = re.sub(r"\s+", "_", no_diacritics)
    cleaned = _SLUG_ALLOWED_RE.sub("_", spaced)
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")

    if not cleaned:
        raise ValueError(
            "Title is not usable after normalization (only unsupported characters)."
        )

    return cleaned


def _write_metadata(path: Path, meta: TextMetadata) -> None:
    payload = asdict(meta)
    payload["created_at"] = meta.created_at.isoformat()
    out = yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)
    path.write_text(out, encoding="utf-8")


def _resolve_authors(nicknames: list[str]) -> list[Author]:
    if not nicknames:
        raise ValueError("At least one --author=<nickname> is required.")

    authors_by_nick = load_authors()
    unique: list[str] = []
    seen: set[str] = set()

    for n in nicknames:
        nick = str(n).strip()
        if not nick:
            continue
        if nick in seen:
            continue
        seen.add(nick)
        unique.append(nick)

    missing = [n for n in unique if n not in authors_by_nick]
    if missing:
        missing_str = ", ".join(missing)
        raise ValueError(f"Unknown author nickname(s): {missing_str}")

    return [authors_by_nick[n] for n in unique]


def create_text(*, title: str, root: Path, author_nicknames: list[str]) -> Path:
    root = root.expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"Root directory does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Root path is not a directory: {root}")

    slug = normalize_title(title)
    target = root / slug
    if target.exists():
        raise FileExistsError(f"Target directory already exists: {target}")

    authors = _resolve_authors(author_nicknames)

    target.mkdir(parents=True, exist_ok=False)
    (target / "stages").mkdir(parents=True, exist_ok=False)
    (target / "text.md").write_text("", encoding="utf-8")

    meta = TextMetadata(
        id=str(uuid.uuid4()),
        title=title,
        slug=slug,
        created_at=datetime.now().astimezone(),
        authors=authors,
    )
    _write_metadata(target / "metadata.yaml", meta)

    return target

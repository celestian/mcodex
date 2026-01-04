from __future__ import annotations

import re
import unicodedata
import uuid
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import yaml

from mcodex.config import find_repo_root, get_text_prefix, load_authors
from mcodex.metadata import LATEST_METADATA_VERSION
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
    payload["metadata_version"] = LATEST_METADATA_VERSION
    payload["created_at"] = meta.created_at.isoformat()
    out = yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)
    path.write_text(out, encoding="utf-8")


def _resolve_authors(*, start: Path, nicknames: list[str]) -> list[Author]:
    if not nicknames:
        raise ValueError("At least one --author=<nickname> is required.")

    repo_root = find_repo_root(start)
    authors_by_nick = load_authors(repo_root=repo_root)
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

    repo_root = find_repo_root(root)
    prefix = get_text_prefix(repo_root=repo_root)

    slug = normalize_title(title)
    dir_name = f"{prefix}{slug}"
    target = root / dir_name
    if target.exists():
        raise FileExistsError(f"Target directory already exists: {target}")

    authors = _resolve_authors(start=root, nicknames=author_nicknames)

    templates_dir = repo_root / ".mcodex" / "templates" / "text"
    todo_tpl = templates_dir / "todo.md"
    checklist_tpl = templates_dir / "checklist.md"

    if not todo_tpl.exists() or not checklist_tpl.exists():
        raise FileNotFoundError(
            "Missing text templates under .mcodex/templates/text/. "
            "Run `mcodex init` first."
        )

    target.mkdir(parents=True, exist_ok=False)

    (target / "text.md").write_text("", encoding="utf-8")

    todo_text = todo_tpl.read_text(encoding="utf-8")
    (target / "todo.md").write_text(todo_text, encoding="utf-8")

    checklist_text = checklist_tpl.read_text(encoding="utf-8")
    (target / "checklist.md").write_text(checklist_text, encoding="utf-8")

    snap_root = target / ".snapshot"
    snap_root.mkdir(parents=True, exist_ok=False)
    (snap_root / ".gitkeep").write_text("", encoding="utf-8")

    meta = TextMetadata(
        id=str(uuid.uuid4()),
        title=title,
        slug=slug,
        created_at=datetime.now().astimezone(),
        authors=authors,
    )
    _write_metadata(target / "metadata.yaml", meta)

    return target

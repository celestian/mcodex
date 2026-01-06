from __future__ import annotations

import importlib.resources
from pathlib import Path

from mcodex.services.init_repo import init_repo


def _read_packaged_template_bytes(rel_path: str) -> bytes:
    traversable = importlib.resources.files("mcodex.package_templates").joinpath(
        "templates",
        rel_path,
    )
    with importlib.resources.as_file(traversable) as p:
        return Path(p).read_bytes()


def test_init_does_not_overwrite_existing_templates(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)

    init_repo(repo_root)

    todo_path = repo_root / ".mcodex" / "templates" / "text" / "todo.md"
    original = todo_path.read_text(encoding="utf-8")

    todo_path.write_text("custom todo\n", encoding="utf-8")

    init_repo(repo_root)

    assert todo_path.read_text(encoding="utf-8") == "custom todo\n"
    assert todo_path.read_text(encoding="utf-8") != original


def test_init_force_overwrites_existing_templates(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)

    init_repo(repo_root)

    todo_path = repo_root / ".mcodex" / "templates" / "text" / "todo.md"
    todo_path.write_text("custom todo\n", encoding="utf-8")

    init_repo(repo_root, force=True)

    expected = _read_packaged_template_bytes("text/todo.md")
    assert todo_path.read_bytes() == expected

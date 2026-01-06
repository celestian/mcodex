from __future__ import annotations

from pathlib import Path

from mcodex.services.init_repo import init_repo


def test_init_copies_templates_into_repo(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)

    init_repo(repo_root)

    templates_root = repo_root / ".mcodex" / "templates"

    assert (templates_root / "text" / "todo.md").exists()
    assert (templates_root / "text" / "checklist.md").exists()
    assert (templates_root / "text" / "README.txt").exists()

    assert (templates_root / "latex" / "main.tex").exists()

    assert (templates_root / "pandoc" / "reference.docx").exists()
    assert (templates_root / "pandoc" / "template.tex").exists()

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from mcodex.services.author import author_add
from mcodex.services.create_text import create_text, normalize_title


@pytest.fixture(autouse=True)
def in_repo(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / ".mcodex").mkdir(parents=True)
    (repo / ".mcodex" / "config.yaml").write_text("{}\n", encoding="utf-8")
    monkeypatch.chdir(repo)
    return repo


def test_normalize_title_removes_diacritics_and_spaces() -> None:
    assert normalize_title("  Článek o něčem  ") == "clanek_o_necem"


def test_normalize_title_rejects_empty() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        normalize_title("   ")


def test_create_text_creates_structure_and_metadata(in_repo: Path) -> None:
    author_add(
        nickname="Novy",
        first_name="Jan",
        last_name="Novák",
        email="jan.novak@example.com",
    )
    author_add(
        nickname="eva",
        first_name="Eva Marie",
        last_name="Svobodová",
        email="eva@example.com",
    )

    root = in_repo / "texts"
    root.mkdir()

    target = create_text(
        title="Článek o něčem",
        root=root,
        author_nicknames=["Novy", "eva"],
    )

    assert target.exists()
    assert (target / "text.md").exists()
    assert (target / "stages").is_dir()
    assert (target / "metadata.yaml").exists()

    data = yaml.safe_load((target / "metadata.yaml").read_text(encoding="utf-8"))
    assert data["metadata_version"] == 1
    assert data["title"] == "Článek o něčem"
    assert data["slug"] == "clanek_o_necem"
    assert isinstance(data["id"], str) and data["id"]
    assert isinstance(data["created_at"], str) and data["created_at"]

    authors = data["authors"]
    assert isinstance(authors, list)
    assert [a["nickname"] for a in authors] == ["Novy", "eva"]
    assert authors[0]["first_name"] == "Jan"
    assert authors[1]["first_name"] == "Eva Marie"


def test_create_text_rejects_unknown_author(in_repo: Path) -> None:
    root = in_repo / "texts"
    root.mkdir()

    with pytest.raises(ValueError, match="Unknown author nickname"):
        create_text(
            title="Test",
            root=root,
            author_nicknames=["missing"],
        )


def test_create_text_rejects_existing_target_dir(in_repo: Path) -> None:
    author_add(
        nickname="Novy",
        first_name="Jan",
        last_name="Novák",
        email="jan.novak@example.com",
    )

    root = in_repo / "texts"
    root.mkdir()

    first = create_text(
        title="Duplicitní",
        root=root,
        author_nicknames=["Novy"],
    )
    assert first.exists()

    with pytest.raises(FileExistsError):
        create_text(
            title="Duplicitní",
            root=root,
            author_nicknames=["Novy"],
        )

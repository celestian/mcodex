from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from mcodex.services.author import author_add
from mcodex.services.text_authors import text_author_add, text_author_remove


@pytest.fixture(autouse=True)
def in_repo(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / ".mcodex").mkdir(parents=True)
    (repo / ".mcodex" / "config.yaml").write_text("{}\n", encoding="utf-8")
    monkeypatch.chdir(repo)
    return repo


def test_text_author_add_and_remove_upgrades_metadata(in_repo: Path) -> None:
    author_add(
        nickname="Novy",
        first_name="Jan",
        last_name="Novák",
        email="jan.novak@example.com",
    )

    text_dir = in_repo / "text1"
    text_dir.mkdir()

    (text_dir / "metadata.yaml").write_text(
        yaml.safe_dump(
            {
                "id": "x",
                "title": "T",
                "slug": "t",
                "created_at": "2026-01-03T00:00:00+01:00",
                "authors": [],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )

    text_author_add(text_dir=text_dir, nickname="Novy")

    data = yaml.safe_load((text_dir / "metadata.yaml").read_text(encoding="utf-8"))
    assert data["metadata_version"] == 1
    assert [a["nickname"] for a in data["authors"]] == ["Novy"]

    text_author_remove(text_dir=text_dir, nickname="Novy")

    data2 = yaml.safe_load((text_dir / "metadata.yaml").read_text(encoding="utf-8"))
    assert data2["metadata_version"] == 1
    assert data2["authors"] == []


def test_text_author_add_unknown_author(in_repo: Path) -> None:
    text_dir = in_repo / "text1"
    text_dir.mkdir()
    (text_dir / "metadata.yaml").write_text(
        yaml.safe_dump(
            {
                "id": "x",
                "title": "T",
                "slug": "t",
                "created_at": "2026-01-03T00:00:00+01:00",
                "authors": [],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Unknown author nickname"):
        text_author_add(text_dir=text_dir, nickname="missing")

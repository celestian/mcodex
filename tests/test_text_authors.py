from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from mcodex.services.author import author_add
from mcodex.services.text_authors import text_author_add, text_author_remove


@pytest.fixture()
def config_path(tmp_path: Path) -> Path:
    return tmp_path / "config.yaml"


@pytest.fixture(autouse=True)
def patch_config_path(monkeypatch: pytest.MonkeyPatch, config_path: Path) -> None:
    from mcodex import config as config_module

    monkeypatch.setattr(config_module, "default_config_path", lambda: config_path)


def test_text_author_add_and_remove(tmp_path: Path) -> None:
    author_add(
        nickname="Novy",
        first_name="Jan",
        last_name="Novák",
        email="jan.novak@example.com",
    )

    text_dir = tmp_path / "text1"
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
    assert [a["nickname"] for a in data["authors"]] == ["Novy"]

    text_author_remove(text_dir=text_dir, nickname="Novy")

    data2 = yaml.safe_load((text_dir / "metadata.yaml").read_text(encoding="utf-8"))
    assert data2["authors"] == []


def test_text_author_add_unknown_author(tmp_path: Path) -> None:
    text_dir = tmp_path / "text1"
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

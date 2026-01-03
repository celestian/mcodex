from __future__ import annotations

from pathlib import Path

import pytest

from mcodex.services.author import author_add, author_list


@pytest.fixture()
def config_path(tmp_path: Path) -> Path:
    return tmp_path / "config.yaml"


@pytest.fixture(autouse=True)
def patch_config_path(monkeypatch: pytest.MonkeyPatch, config_path: Path) -> None:
    from mcodex import config as config_module

    monkeypatch.setattr(config_module, "default_config_path", lambda: config_path)


def test_author_add_and_list_prints(capsys: pytest.CaptureFixture[str]) -> None:
    author_add(
        nickname="celestian",
        first_name="Jan",
        last_name="Novák",
        email="jan.novak@example.com",
    )

    author_list()
    out = capsys.readouterr().out.strip()

    assert out == "Jan Novák (@celestian) <jan.novak@example.com>"


def test_author_add_rejects_duplicate_nickname() -> None:
    author_add(
        nickname="eva",
        first_name="Eva",
        last_name="Svobodová",
        email="eva@example.com",
    )

    with pytest.raises(ValueError, match="already exists"):
        author_add(
            nickname="eva",
            first_name="Eva",
            last_name="Svobodová",
            email="eva2@example.com",
        )


def test_author_add_rejects_uppercase_nickname() -> None:
    with pytest.raises(ValueError, match="lowercase"):
        author_add(
            nickname="Eva",
            first_name="Eva",
            last_name="Svobodová",
            email="eva@example.com",
        )


def test_author_add_rejects_bad_email() -> None:
    with pytest.raises(ValueError, match="Email must look like"):
        author_add(
            nickname="badmail",
            first_name="Bad",
            last_name="Mail",
            email="not-an-email",
        )


def test_author_list_empty(capsys: pytest.CaptureFixture[str]) -> None:
    author_list()
    out = capsys.readouterr().out.strip()
    assert out == "No authors found."

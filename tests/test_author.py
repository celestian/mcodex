from __future__ import annotations

from pathlib import Path

import pytest

from mcodex.errors import (
    AuthorAlreadyExistsError,
    AuthorNotFoundError,
    InvalidEmailError,
    InvalidNicknameError,
)
from mcodex.services.author import author_add, author_list, author_remove


@pytest.fixture(autouse=True)
def in_repo(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / ".mcodex").mkdir(parents=True)
    (repo / ".mcodex" / "config.yaml").write_text("{}\n", encoding="utf-8")
    monkeypatch.chdir(repo)


def test_author_add_and_list_prints(capsys: pytest.CaptureFixture[str]) -> None:
    author_add(
        nickname="Novy",
        first_name="Jan",
        last_name="Novák",
        email="jan.novak@example.com",
    )

    author_list()
    out = capsys.readouterr().out.strip()

    assert out == "Jan Novák (@Novy) <jan.novak@example.com>"


def test_author_add_rejects_duplicate_nickname() -> None:
    author_add(
        nickname="eva",
        first_name="Eva",
        last_name="Svobodová",
        email="eva@example.com",
    )

    with pytest.raises(AuthorAlreadyExistsError):
        author_add(
            nickname="eva",
            first_name="Eva",
            last_name="Svobodová",
            email="eva2@example.com",
        )


def test_author_add_rejects_invalid_nickname_characters() -> None:
    with pytest.raises(InvalidNicknameError):
        author_add(
            nickname="eva nová",
            first_name="Eva",
            last_name="Svobodová",
            email="eva@example.com",
        )


def test_author_add_rejects_bad_email() -> None:
    with pytest.raises(InvalidEmailError):
        author_add(
            nickname="badmail",
            first_name="Bad",
            last_name="Mail",
            email="not-an-email",
        )


def test_author_remove_makes_list_empty(capsys: pytest.CaptureFixture[str]) -> None:
    author_add(
        nickname="Novy",
        first_name="Jan",
        last_name="Novák",
        email="jan.novak@example.com",
    )
    author_remove(nickname="Novy")

    author_list()
    out = capsys.readouterr().out.strip()
    assert out == "No authors found."


def test_author_remove_missing() -> None:
    with pytest.raises(AuthorNotFoundError):
        author_remove(nickname="missing")


def test_author_list_empty(capsys: pytest.CaptureFixture[str]) -> None:
    author_list()
    out = capsys.readouterr().out.strip()
    assert out == "No authors found."

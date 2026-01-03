from __future__ import annotations

import re

from mcodex.config import load_authors, save_authors
from mcodex.models import Author

_NICK_RE = re.compile(r"^[a-zA-Z0-9_]+$")


def _validate_nickname(nickname: str) -> str:
    nick = nickname.strip()
    if not nick:
        raise ValueError("Nickname must not be empty.")
    if not _NICK_RE.fullmatch(nick):
        raise ValueError("Nickname must match: [a-zA-Z0-9_]+")
    return nick


def _validate_email(email: str) -> str:
    e = email.strip()
    if not e or "@" not in e:
        raise ValueError("Email must look like an email address.")
    return e


def author_add(*, nickname: str, first_name: str, last_name: str, email: str) -> None:
    nick = _validate_nickname(nickname)
    first = first_name.strip()
    last = last_name.strip()
    mail = _validate_email(email)

    if not first:
        raise ValueError("First name must not be empty.")
    if not last:
        raise ValueError("Last name must not be empty.")

    authors = load_authors()
    if nick in authors:
        raise ValueError(f"Author nickname already exists: {nick}")

    authors[nick] = Author(
        nickname=nick,
        first_name=first,
        last_name=last,
        email=mail,
    )
    save_authors(authors)


def author_remove(*, nickname: str) -> None:
    nick = _validate_nickname(nickname)
    authors = load_authors()

    if nick not in authors:
        raise ValueError(f"Author nickname not found: {nick}")

    del authors[nick]
    save_authors(authors)


def author_list() -> None:
    authors = load_authors()
    if not authors:
        print("No authors found.")
        return

    for nick in sorted(authors.keys()):
        print(authors[nick].display_name)

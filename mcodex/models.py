from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Author:
    nickname: str
    first_name: str
    last_name: str
    email: str

    @property
    def display_name(self) -> str:
        return f"{self.first_name} {self.last_name} (@{self.nickname}) <{self.email}>"


@dataclass(frozen=True)
class TextMetadata:
    id: str
    title: str
    slug: str
    created_at: datetime
    authors: list[Author]

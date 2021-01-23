from __future__ import annotations

from typing import Protocol

from .data import Passage, SearchResults, VerseRange


class Bible(Protocol):
    command: str
    name: str
    abbr: str
    service: str
    service_version: str
    rtl: bool | None
    books: int


class Service(Protocol):
    async def get_passage(self, bible: Bible, verses: VerseRange) -> Passage:
        ...

    async def search(
        self,
        bible: Bible,
        terms: list[str],
        *,
        limit: int = ...,
        offset: int = ...,
    ) -> SearchResults:
        ...

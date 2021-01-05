from __future__ import annotations

from typing import List, Optional, Protocol

from .data import Passage, SearchResults, VerseRange


class Bible(Protocol):
    command: str
    name: str
    abbr: str
    service: str
    service_version: str
    rtl: Optional[bool]
    books: int


class Service(Protocol):
    async def get_passage(self, bible: Bible, verses: VerseRange) -> Passage:
        ...

    async def search(
        self, bible: Bible, terms: List[str], *, limit: int = -1, offset: int = -1
    ) -> SearchResults:
        ...

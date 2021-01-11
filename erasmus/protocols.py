from __future__ import annotations

from typing import List, Optional, Protocol

import aiohttp

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
    async def get_passage(
        self, session: aiohttp.ClientSession, bible: Bible, verses: VerseRange
    ) -> Passage:
        ...

    async def search(
        self,
        session: aiohttp.ClientSession,
        bible: Bible,
        terms: List[str],
        *,
        limit: int = ...,
        offset: int = ...,
    ) -> SearchResults:
        ...

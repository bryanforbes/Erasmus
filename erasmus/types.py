from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, TypeAlias, runtime_checkable

from sqlalchemy.orm import sessionmaker

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from .data import Passage, SearchResults, VerseRange

    AsyncSessionMaker: TypeAlias = sessionmaker['AsyncSession']  # type: ignore
else:
    AsyncSessionMaker: TypeAlias = sessionmaker


class Bible(Protocol):
    @property
    def id(self) -> int:
        ...

    @property
    def command(self) -> str:
        ...

    @property
    def name(self) -> str:
        ...

    @property
    def abbr(self) -> str:
        ...

    @property
    def service(self) -> str:
        ...

    @property
    def service_version(self) -> str:
        ...

    @property
    def rtl(self) -> bool | None:
        ...

    @property
    def books(self) -> int:
        ...

    @property
    def book_mapping(self) -> dict[str, str] | None:
        ...


class Service(Protocol):
    async def get_passage(self, bible: Bible, verses: VerseRange, /) -> Passage:
        ...

    async def search(
        self,
        bible: Bible,
        terms: list[str],
        /,
        *,
        limit: int = ...,
        offset: int = ...,
    ) -> SearchResults:
        ...


@runtime_checkable
class Refreshable(Protocol):
    async def refresh(self, session: AsyncSession, /) -> None:
        ...

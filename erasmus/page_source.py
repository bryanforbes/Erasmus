from __future__ import annotations

import inspect
from abc import abstractmethod
from collections.abc import AsyncIterable, Awaitable, Callable, Iterable, Sequence
from typing import NotRequired, Protocol, TypedDict, override, runtime_checkable

import discord

type MaybeAwaitable[**P, T] = Callable[P, T | Awaitable[T]]


async def _maybe_await[
    **P, T
](f: MaybeAwaitable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
    value = f(*args, **kwargs)
    if inspect.isawaitable(value):
        return await value

    return value


class Kwargs(TypedDict):
    content: NotRequired[str]
    embeds: NotRequired[Sequence[discord.Embed]]


class Pages[T](Protocol):
    source: PageSource[T]
    current_page: int


class BasePages[T](Pages[T]):
    source: PageSource[T]
    current_page: int

    def __init__(self, source: PageSource[T], /) -> None:
        self.source = source
        self.current_page = 0

    async def _get_kwargs_from_page(self, page: T | None, /) -> Kwargs:
        value = await self.source.format_page(self, page)
        if isinstance(value, discord.Embed):
            return {'embeds': [value]}

        if isinstance(value, str):
            return {'content': value}

        return value


class PageSource[T](Protocol):
    _prepared: bool

    async def _prepare_once(self, /) -> None:
        try:
            # Don't feel like formatting hasattr with
            # the proper mangling
            # read this as follows:
            # if hasattr(self, '__prepare')
            # except that it works as you expect
            self._prepared  # noqa: B018
        except AttributeError:
            await self.prepare()
            self._prepared = True

    async def prepare(self, /) -> None:
        return

    @property
    @abstractmethod
    def needs_pagination(self, /) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get_max_pages(self, /) -> int:
        raise NotImplementedError

    @abstractmethod
    def get_total(self, /) -> int:
        raise NotImplementedError

    @abstractmethod
    async def get_page(self, page_number: int, /) -> T:
        raise NotImplementedError

    @abstractmethod
    async def format_page(
        self, pages: Pages[T], page: T | None, /
    ) -> str | discord.Embed | Kwargs:
        raise NotImplementedError


class PageSourceBase[T](PageSource[T]):
    _prepared: bool


class ListPageSource[T](PageSourceBase[Sequence[T]]):
    entries: Sequence[T]
    per_page: int
    _total: int
    _max_pages: int

    def __init__(self, entries: Sequence[T], /, *, per_page: int) -> None:
        self.entries = entries
        self.per_page = per_page
        self._total = len(entries)

        pages, left_over = divmod(self._total, per_page)
        if left_over:
            pages += 1

        self._max_pages = pages

    @property
    @override
    def needs_pagination(self) -> bool:
        return len(self.entries) > self.per_page

    @override
    def get_max_pages(self) -> int:
        return self._max_pages

    @override
    def get_total(self) -> int:
        return self._total

    @override
    async def get_page(self, page_number: int, /) -> Sequence[T]:
        base = page_number * self.per_page
        return self.entries[base : base + self.per_page]


@runtime_checkable
class Page[T](Iterable[T], Protocol):
    @property
    def total(self) -> int: ...


@runtime_checkable
class AsyncPage[T](AsyncIterable[T], Protocol):
    @property
    def total(self) -> int: ...


async def _iterable_to_list[T](page: Iterable[T] | AsyncIterable[T]) -> list[T]:
    if isinstance(page, AsyncIterable):
        return [item async for item in page]

    return list(page)


class AsyncCallback[T](Protocol):
    def __call__(
        self, /, *, per_page: int, page_number: int
    ) -> Awaitable[Page[T]] | AsyncPage[T]: ...


class AsyncPageSource[T](PageSourceBase[Sequence[T]]):
    per_page: int
    _total: int
    _max_pages: int
    _callback: AsyncCallback[T]
    _cache: dict[int, Sequence[T]]

    def __init__(self, callback: AsyncCallback[T], /, *, per_page: int) -> None:
        self._callback = callback
        self.per_page = per_page
        self._cache = {}

    @override
    async def prepare(self, /) -> None:
        await super().prepare()

        initial_page = await _maybe_await(
            self._callback, per_page=self.per_page, page_number=0
        )
        max_pages, left_over = divmod(initial_page.total, self.per_page)

        if left_over:
            max_pages += 1

        self._total = initial_page.total
        self._max_pages = max_pages

        items = await _iterable_to_list(initial_page)

        if len(items) == self._total:
            for page in range(self._max_pages):
                page_start = page * self.per_page
                self._cache[page] = items[page_start : page_start * self.per_page]
        else:
            self._cache[0] = items

    @property
    @override
    def needs_pagination(self, /) -> bool:
        return self._total > self.per_page

    @override
    def get_max_pages(self, /) -> int:
        return self._max_pages

    @override
    def get_total(self, /) -> int:
        return self._total

    @override
    async def get_page(self, page_number: int, /) -> Sequence[T]:
        if page_number in self._cache:
            return self._cache[page_number]

        page = await _maybe_await(
            self._callback,
            per_page=self.per_page,
            page_number=page_number * self.per_page,
        )

        self._cache[page_number] = await _iterable_to_list(page)

        return self._cache[page_number]


class EmbedPageSource[T](PageSourceBase[T]):
    embed: discord.Embed

    @override
    async def prepare(self, /) -> None:
        await super().prepare()

        self.embed = discord.Embed()

    @override
    async def format_page(
        self, pages: Pages[T], page: T | None, /
    ) -> str | discord.Embed | Kwargs:
        self.embed.clear_fields()
        self.embed.description = None

        await self.set_page_text(page)

        if page is not None:
            maximum = self.get_max_pages()
            if maximum > 1:
                text = self.format_footer_text(pages, maximum)
                self.embed.set_footer(text=text)

        return self.embed

    def format_footer_text(self, pages: Pages[T], max_pages: int) -> str:
        return f'Page {pages.current_page + 1}/{max_pages} ({self.get_total()} entries)'

    @abstractmethod
    async def set_page_text(self, page: T | None, /) -> None:
        raise NotImplementedError


class FieldPageSource[T](EmbedPageSource[T]):
    @abstractmethod
    def get_field_values(self, page: T, /) -> Iterable[tuple[str, str]]:
        raise NotImplementedError

    @override
    async def set_page_text(self, page: T | None, /) -> None:
        if page is None:
            self.embed.description = 'I found 0 results'
            return

        for key, value in self.get_field_values(page):
            self.embed.add_field(name=key, value=value, inline=False)

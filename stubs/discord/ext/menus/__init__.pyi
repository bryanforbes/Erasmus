from collections import OrderedDict
from collections.abc import AsyncIterator, Awaitable, Callable, Sequence
from typing import Any, Generic, Literal, NamedTuple, Protocol, TypeVar, overload

import discord
from discord.ext import commands

_AF = TypeVar('_AF', bound=_ButtonCoroutine)
_T = TypeVar('_T')

class _SkipIfCallback(Protocol):
    def __call__(self, __menu: Menu) -> bool: ...

class _ButtonAction(Protocol):
    async def __call__(
        self, __menu: Menu, __payload: discord.RawReactionActionEvent
    ) -> Any: ...

class _ButtonCoroutine(Protocol):
    async def __call__(
        self, __menu: Any, __payload: discord.RawReactionActionEvent
    ) -> Any: ...

class MenuError(Exception): ...

class CannotEmbedLinks(MenuError):
    def __init__(self) -> None: ...

class CannotSendMessages(MenuError):
    def __init__(self) -> None: ...

class CannotAddReactions(MenuError):
    def __init__(self) -> None: ...

class CannotReadMessageHistory(MenuError):
    def __init__(self) -> None: ...

class Position:
    bucket: float
    number: float
    def __init__(self, number: float, *, bucket: float = ...) -> None: ...
    def __lt__(self, other: Any) -> bool: ...
    def __eq__(self, other: Any) -> bool: ...
    def __le__(self, other: Any) -> bool: ...
    def __gt__(self, other: Any) -> bool: ...
    def __ge__(self, other: Any) -> bool: ...

class Last(Position):
    def __init__(self, number: float = ...) -> None: ...

class First(Position):
    def __init__(self, number: float = ...) -> None: ...

class Button:
    emoji: discord.PartialEmoji
    position: Position
    lock: bool
    skip_if: _SkipIfCallback
    action: _ButtonAction
    def __init__(
        self,
        emoji: str | discord.PartialEmoji,
        action: _ButtonAction,
        *,
        skip_if: _SkipIfCallback | None = ...,
        position: Any | None = ...,
        lock: bool = ...,
    ) -> None: ...
    async def __call__(
        self, menu: Menu, payload: discord.RawReactionActionEvent
    ) -> Any: ...
    def is_valid(self, menu: Menu) -> bool: ...

def button(
    emoji: str | discord.PartialEmoji, **kwargs: Any
) -> Callable[[_AF], _AF]: ...

class _MenuMeta(type):
    @classmethod
    def __prepare__(
        metacls, __name: str, __bases: tuple[type, ...], **kwargs: Any
    ) -> OrderedDict[str, Any]: ...
    def __new__(
        metacls,
        name: str,
        bases: tuple[type, ...],
        attrs: OrderedDict[str, Any],
        **kwargs: Any,
    ) -> Any: ...
    def get_buttons(cls) -> OrderedDict[str, Button]: ...

class Menu(metaclass=_MenuMeta):
    timeout: float
    delete_message_after: bool
    clear_reactions_after: bool
    check_embeds: bool
    message: discord.Message
    ctx: commands.Context
    bot: commands.Bot[commands.Context]
    _can_remove_reactions: bool
    _running: bool
    def __init__(
        self,
        *,
        timeout: float = ...,
        delete_message_after: bool = ...,
        clear_reactions_after: bool = ...,
        check_embeds: bool = ...,
        message: discord.Message | None = ...,
    ) -> None: ...
    @discord.utils.cached_property
    def buttons(self) -> dict[str, Button]: ...
    @overload
    def add_button(
        self, button: Button, *, react: Literal[True]
    ) -> Awaitable[None]: ...
    @overload
    def add_button(self, button: Button, *, react: Literal[False] = ...) -> None: ...
    @overload
    def remove_button(
        self, emoji: Button | str | discord.PartialEmoji, *, react: Literal[True]
    ) -> Awaitable[None]: ...
    @overload
    def remove_button(
        self,
        emoji: Button | str | discord.PartialEmoji,
        *,
        react: Literal[False] = ...,
    ) -> None: ...
    @overload
    def clear_buttons(self, *, react: Literal[True]) -> Awaitable[None]: ...
    @overload
    def clear_buttons(self, *, react: Literal[False] = ...) -> None: ...
    def should_add_reactions(self) -> int: ...
    def reaction_check(self, payload: discord.RawReactionActionEvent) -> bool: ...
    async def update(self, payload: discord.RawReactionActionEvent) -> None: ...
    async def start(
        self,
        ctx: commands.Context,
        *,
        channel: discord.abc.Messageable | None = ...,
        wait: bool = ...,
    ) -> None: ...
    async def finalize(self, timed_out: bool) -> None: ...
    async def send_initial_message(
        self, ctx: commands.Context, channel: discord.abc.Messageable
    ) -> None: ...
    def stop(self) -> None: ...

_PS = TypeVar('_PS', bound=PageSource[Any])

class PageSource(Generic[_T]):
    async def _prepare_once(self) -> None: ...
    async def prepare(self) -> None: ...
    def is_paginating(self) -> bool: ...
    def get_max_pages(self) -> int | None: ...
    async def get_page(self, page_number: int) -> _T: ...
    async def format_page(
        self: _PS, menu: MenuPages[_PS], page: _T
    ) -> str | discord.Embed | dict[str, Any]: ...

_S = TypeVar('_S', bound=PageSource[Any])

class MenuPages(Menu, Generic[_S]):
    current_page: int
    def __init__(
        self,
        source: _S,
        *,
        timeout: float = ...,
        delete_message_after: bool = ...,
        clear_reactions_after: bool = ...,
        check_embeds: bool = ...,
        message: discord.Message | None = ...,
    ) -> None: ...
    @property
    def source(self) -> _S: ...
    async def change_source(self, source: _S) -> None: ...
    def should_add_reactions(self) -> bool: ...
    async def show_page(self, page_number: int) -> None: ...
    async def send_initial_message(
        self, ctx: commands.Context, channel: discord.abc.Messageable
    ) -> Any: ...
    async def start(
        self,
        ctx: commands.Context,
        *,
        channel: discord.abc.Messageable | None = ...,
        wait: bool = ...,
    ) -> None: ...
    async def show_checked_page(self, page_number: int) -> None: ...
    async def show_current_page(self) -> None: ...
    async def go_to_first_page(
        self, payload: discord.RawReactionActionEvent
    ) -> None: ...
    async def go_to_previous_page(
        self, payload: discord.RawReactionActionEvent
    ) -> None: ...
    async def go_to_next_page(
        self, payload: discord.RawReactionActionEvent
    ) -> None: ...
    async def go_to_last_page(
        self, payload: discord.RawReactionActionEvent
    ) -> None: ...
    async def stop_pages(self, payload: discord.RawReactionActionEvent) -> None: ...

class ListPageSource(PageSource[Sequence[_T]]):
    entries: Sequence[_T]
    per_page: int
    def __init__(self, entries: Sequence[_T], *, per_page: int) -> None: ...
    def is_paginating(self) -> bool: ...
    def get_max_pages(self) -> int: ...
    async def get_page(  # type: ignore[override]
        self, page_number: int
    ) -> _T | Sequence[_T]: ...

class _GroupByEntry(Generic[_T]):
    key: Any
    items: Sequence[_T]

_GBS = TypeVar('_GBS', bound=GroupByPageSource[Any])

class GroupByPageSource(ListPageSource[_GroupByEntry[_T]], Generic[_T]):
    nested_per_page: int
    def __init__(
        self,
        entries: Sequence[_T],
        *,
        key: Callable[[Any], Any],
        per_page: int,
        sort: bool = ...,
    ) -> None: ...
    async def get_page(  # type: ignore[override]
        self, page_number: int
    ) -> _GroupByEntry[_T]: ...
    async def format_page(  # type: ignore[override]
        self: _GBS, menu: MenuPages[_GBS], entry: _GroupByEntry[_T]
    ) -> str | discord.Embed | dict[str, Any]: ...

class AsyncIteratorPageSource(PageSource[_T]):
    iterator: AsyncIterator[_T]
    per_page: int
    def __init__(self, iterator: AsyncIterator[_T], *, per_page: int) -> None: ...
    async def prepare(self, *, _aiter: Any = ...) -> None: ...
    def is_paginating(self) -> bool: ...
    async def get_page(self, page_number: int) -> _T: ...

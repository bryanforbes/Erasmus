from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import TYPE_CHECKING, Any, Final, Generic, Protocol, TypeVar, overload
from typing_extensions import Self

import discord
from attrs import define, field
from botus_receptus import util
from discord import app_commands
from discord.ext import commands

from .data import Passage

if TYPE_CHECKING:
    from .erasmus import Erasmus


_DV_co = TypeVar('_DV_co', covariant=True)
_R_contra = TypeVar('_R_contra', contravariant=True)
_T = TypeVar('_T')
_V = TypeVar('_V', bound='Info[Any]')


_truncation_warning: Final = '**The passage was too long and has been truncated:**\n\n'
_max_length: Final = 4096 - (len(_truncation_warning) + 1)


def _get_passage_text(passage: Passage, /) -> str:
    text = passage.text

    if len(text) > 6000:
        text = f'{_truncation_warning}{text[:_max_length]}\u2026'

    return text


async def send_context_passage(
    ctx: commands.Context[Erasmus],
    passage: Passage,
) -> discord.Message:
    return await util.send_context(
        ctx, description=_get_passage_text(passage), footer={'text': passage.citation}
    )


async def send_interaction_passage(
    interaction: discord.Interaction,
    passage: Passage,
    /,
    *,
    ephemeral: bool = False,
) -> None:
    await util.send_interaction(
        interaction,
        description=_get_passage_text(passage),
        footer={'text': passage.citation},
        ephemeral=ephemeral,
    )


class Descriptor(Protocol[_DV_co]):
    @overload
    def __get__(self, instance: None, owner: Any) -> Self:
        ...

    @overload
    def __get__(self, instance: object, owner: Any) -> _DV_co:
        ...


class Record(Protocol):
    command: Descriptor[str] | str


class Info(Protocol[_R_contra]):
    @property
    def command(self) -> str:
        ...

    @property
    def display_name(self) -> str:
        ...

    def update(self, record: _R_contra, /) -> None:
        ...

    def matches(self, text: str, /) -> bool:
        ...

    @classmethod
    def create(cls, record: _R_contra, /) -> Self:
        ...


@define
class InfoContainer(Generic[_V]):
    info_cls: type[_V]
    _keys: list[str] = field(init=False)
    _map: dict[str, _V] = field(init=False)

    def __attrs_post_init__(self) -> None:
        self._keys = []
        self._map = {}

    def set(self, records: Iterable[Record], /) -> None:
        new_keys: list[str] = []
        new_map: dict[str, _V] = {}

        for record in records:
            info = self.info_cls.create(record)
            new_keys.append(info.command)
            new_map[info.command] = info

        self._keys = sorted(new_keys)
        self._map = new_map

    def clear(self) -> None:
        self._keys.clear()
        self._map.clear()

    def add(self, record: Record, /) -> None:
        info = self.info_cls.create(record)
        self._keys.append(info.command)
        self._map[info.command] = info

    def delete(self, /, *, command: str) -> None:
        self._keys.remove(command)
        del self._map[command]

    def update(self, record: Record, /) -> None:
        info = self._map.get(record.command)
        if info is not None:
            info.update(record)
        else:
            self.add(record)

    @overload
    def get(self, command: str, /) -> _V | None:
        ...

    @overload
    def get(self, command: str, /, default: _T) -> _V | _T:
        ...

    def get(self, command: str, /, default: _T | None = None) -> _V | _T | None:
        return self._map.get(command, default)

    def __iter__(self) -> Iterator[_V]:
        for key in self._keys:
            yield self._map[key]

    def choices(self, current: str, /) -> list[app_commands.Choice[str]]:
        current = current.strip()

        return [
            app_commands.Choice(name=info.display_name, value=info.command)
            for info in self
            if not current or info.matches(current)
        ][:25]

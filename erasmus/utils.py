from __future__ import annotations

from collections import OrderedDict
from typing import TYPE_CHECKING, Final, Generic, Protocol, TypeVar, overload

import discord
from attrs import define, field
from botus_receptus import utils
from discord import app_commands

if TYPE_CHECKING:
    from collections.abc import Iterable

    from discord.ext import commands

    from .data import Passage
    from .erasmus import Erasmus
    from .types import Coroutine


_OptionT = TypeVar('_OptionT', bound='Option')

_truncation_warning: Final = '**The passage was too long and has been truncated:**\n\n'
_description_max_length: Final = 4096
_max_length: Final = _description_max_length - (len(_truncation_warning) + 1)


def _get_passage_text(passage: Passage, /) -> str:
    text = passage.text

    if len(text) > _description_max_length:
        text = f'{_truncation_warning}{text[:_max_length]}\u2026'

    return text


@overload
async def send_passage(
    ctx: commands.Context[Erasmus],
    passage: Passage,
    /,
) -> discord.Message:
    ...


@overload
async def send_passage(
    interaction: discord.Interaction, passage: Passage, /, *, ephemeral: bool = False
) -> discord.Message:
    ...


def send_passage(
    ctx_or_intx: commands.Context[Erasmus] | discord.Interaction,
    passage: Passage,
    /,
    ephemeral: bool = discord.utils.MISSING,
) -> Coroutine[discord.Message]:
    return utils.send_embed(
        ctx_or_intx,
        description=_get_passage_text(passage),
        footer={'text': passage.citation},
        ephemeral=ephemeral,
    )


class Option(Protocol):
    @property
    def key(self) -> str:
        ...

    @property
    def name(self) -> str:
        ...

    def matches(self, text: str, /) -> bool:
        ...

    def choice(self) -> app_commands.Choice[str]:
        ...


@define(eq=False)
class AutoCompleter(app_commands.Transformer, Generic[_OptionT]):
    _storage: OrderedDict[str, _OptionT] = field(init=False)

    def __attrs_post_init__(self) -> None:
        self._storage = OrderedDict()

    def add(self, option: _OptionT, /) -> None:
        self._storage[option.key] = option

    def update(self, options: Iterable[_OptionT], /) -> None:
        for option in options:
            self.add(option)

    def clear(self) -> None:
        self._storage.clear()

    def discard(self, key: str, /) -> None:
        if key in self._storage:
            del self._storage[key]

    def remove(self, key: str, /) -> None:
        if key not in self._storage:
            raise KeyError(key)

        self.discard(key)

    def get(self, key: str, /) -> _OptionT | None:
        return self._storage.get(key)

    def generate_choices(self, current: str, /) -> list[app_commands.Choice[str]]:
        current = current.lower().strip()

        return [
            option.choice()
            for option in self._storage.values()
            if not current or option.matches(current)
        ][:25]

    async def transform(self, interaction: discord.Interaction, value: str) -> str:
        return value

    async def autocomplete(  # type: ignore
        self, interaction: discord.Interaction, value: str
    ) -> list[app_commands.Choice[str]]:
        value = value.lower().strip()

        return [
            option.choice()
            for option in self._storage.values()
            if not value or option.matches(value)
        ][:25]

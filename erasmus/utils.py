from __future__ import annotations

from collections import OrderedDict
from typing import (
    TYPE_CHECKING,
    Final,
    NotRequired,
    Protocol,
    TypedDict,
    Unpack,
    overload,
    override,
)

from attrs import field, frozen
from botus_receptus import utils
from discord import app_commands

if TYPE_CHECKING:
    from collections.abc import Iterable

    import discord
    from botus_receptus.types import Coroutine

    from .data import Passage

_truncation_warning: Final = '**The passage was too long and has been truncated:**\n\n'
_description_max_length: Final = 4096
_max_length: Final = _description_max_length - (len(_truncation_warning) + 1)


def _get_passage_text(passage: Passage, /) -> str:
    text = passage.text

    if len(text) > _description_max_length:
        text = f'{_truncation_warning}{text[:_max_length]}\u2026'

    return text


class SendPassageBaseKwargs(TypedDict):
    title: NotRequired[str | None]


class SendPassageInteractionKwargs(SendPassageBaseKwargs):
    ephemeral: NotRequired[bool]


class SendPassageWebhookKwargs(SendPassageInteractionKwargs):
    username: NotRequired[str]
    avatar_url: NotRequired[str]
    thread: NotRequired[discord.Object | discord.Thread]


@overload
async def send_passage(
    msg: discord.abc.Messageable | discord.Message,
    passage: Passage,
    /,
    **kwargs: Unpack[SendPassageBaseKwargs],
) -> discord.Message: ...


@overload
async def send_passage(
    itx: discord.Webhook,
    passage: Passage,
    /,
    **kwargs: Unpack[SendPassageWebhookKwargs],
) -> discord.WebhookMessage: ...


@overload
async def send_passage(
    itx: discord.Interaction,
    passage: Passage,
    /,
    **kwargs: Unpack[SendPassageInteractionKwargs],
) -> discord.Message: ...


@overload
async def send_passage(
    itx: (
        discord.abc.Messageable
        | discord.Message
        | discord.Webhook
        | discord.Interaction
    ),
    passage: Passage,
    /,
    **kwargs: Unpack[SendPassageWebhookKwargs],
) -> discord.Message: ...


def send_passage(
    msg_or_itx: (
        discord.abc.Messageable
        | discord.Message
        | discord.Webhook
        | discord.Interaction
    ),
    passage: Passage,
    /,
    **kwargs: Unpack[SendPassageWebhookKwargs],
) -> Coroutine[discord.Message]:
    return utils.send_embed(
        msg_or_itx,
        description=_get_passage_text(passage),
        footer={'text': passage.citation},
        **kwargs,
    )


class Option(Protocol):
    @property
    def key(self) -> str: ...

    @property
    def name(self) -> str: ...

    def matches(self, text: str, /) -> bool: ...

    def choice(self) -> app_commands.Choice[str]: ...


@frozen(eq=False)
class AutoCompleter[OptionT: Option](app_commands.Transformer):
    _storage: OrderedDict[str, OptionT] = field(
        init=False, factory=lambda: OrderedDict[str, OptionT]()
    )

    def add(self, option: OptionT, /) -> None:
        self._storage[option.key] = option

    def update(self, options: Iterable[OptionT], /) -> None:
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

    def get(self, key: str, /) -> OptionT | None:
        return self._storage.get(key)

    def generate_choices(self, current: str, /) -> list[app_commands.Choice[str]]:
        current = current.lower().strip()

        return [
            option.choice()
            for option in self._storage.values()
            if not current or option.matches(current)
        ][:25]

    @override
    async def transform(self, itx: discord.Interaction, value: str, /) -> str:
        return value

    @override
    async def autocomplete(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, itx: discord.Interaction, value: str, /
    ) -> list[app_commands.Choice[str]]:
        value = value.lower().strip()

        return [
            option.choice()
            for option in self._storage.values()
            if not value or option.matches(value)
        ][:25]

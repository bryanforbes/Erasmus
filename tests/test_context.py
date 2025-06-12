from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import pytest
from attrs import define, field
from botus_receptus import Embed
from discord.ext.commands.view import (  # pyright: ignore[reportMissingTypeStubs]
    StringView,
)

from erasmus.context import Context

if TYPE_CHECKING:
    import unittest.mock

    import discord

    from erasmus.erasmus import Erasmus

    from .types import MockerFixture


@define
class MockUser:
    bot: bool | None = field(default=None)
    id: int | None = field(default=None)
    mention: str | None = field(default=None)


@define
class MockMessage:
    author: MockUser | None = field(default=None)
    content: str | None = field(default=None)
    channel: discord.abc.GuildChannel | None = field(default=None)
    _state: Any = field(default=None)


class TestContext:
    @pytest.fixture
    def mock_context_send(self, mocker: MockerFixture) -> unittest.mock.AsyncMock:
        return mocker.patch('discord.ext.commands.Context.send')

    @pytest.fixture
    def string_view(self) -> StringView:
        return StringView('')

    async def test_send_embed(
        self,
        mock_context_send: unittest.mock.AsyncMock,
        string_view: StringView,
    ) -> None:
        ctx = Context(
            prefix='~',
            message=cast('discord.Message', MockMessage()),
            view=string_view,
            bot=cast('Erasmus', object()),
        )

        await ctx.send_embed('baz')

        assert isinstance(mock_context_send.call_args_list[0][1]['embeds'][0], Embed)

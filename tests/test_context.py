from __future__ import annotations

import unittest.mock
from typing import cast

import discord
import pytest
import pytest_mock
from botus_receptus import Embed
from discord.ext.commands.view import StringView  # type: ignore

from erasmus.context import Context
from erasmus.erasmus import Erasmus


class MockUser(object):
    __slots__ = ('bot', 'id', 'mention')

    def __init__(
        self,
        *,
        bot: bool | None = None,
        id: int | None = None,
        mention: str | None = None,
    ) -> None:
        self.bot = bot
        self.id = id
        self.mention = mention


class MockMessage(object):
    __slots__ = ('author', 'content', 'channel', '_state')
    channel: discord.abc.GuildChannel | None

    def __init__(
        self, *, author: MockUser | None = None, content: str | None = None
    ) -> None:
        self.author = author
        self.content = content
        self.channel = None
        self._state = None


class TestContext(object):
    @pytest.fixture
    def mock_context_send(
        self, mocker: pytest_mock.MockFixture
    ) -> unittest.mock.AsyncMock:
        return mocker.patch('discord.ext.commands.Context.send')

    @pytest.fixture
    def string_view(self) -> StringView:
        return StringView('')

    async def test_send_embed(
        self,
        mocker: pytest_mock.MockFixture,
        mock_context_send: unittest.mock.AsyncMock,
        string_view: StringView,
    ) -> None:
        ctx = Context(
            prefix='~',
            message=cast(discord.Message, MockMessage()),
            view=string_view,
            bot=cast(Erasmus, object()),
        )

        await ctx.send_embed('baz')

        assert isinstance(mock_context_send.call_args_list[0][1]['embeds'][0], Embed)

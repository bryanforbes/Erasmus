from __future__ import annotations

import unittest.mock
from typing import Any, Optional, cast

import discord
import pytest
import pytest_mock

from erasmus.context import Context


class MockUser(object):
    __slots__ = ('bot', 'id', 'mention')

    def __init__(
        self,
        *,
        bot: Optional[bool] = None,
        id: Optional[int] = None,
        mention: Optional[str] = None,
    ) -> None:
        self.bot = bot
        self.id = id
        self.mention = mention


class MockMessage(object):
    __slots__ = ('author', 'content', 'channel', '_state')
    channel: Optional[discord.abc.GuildChannel]

    def __init__(
        self, *, author: Optional[MockUser] = None, content: Optional[str] = None
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

    @pytest.mark.asyncio
    async def test_send_embed(
        self,
        mocker: pytest_mock.MockFixture,
        mock_context_send: unittest.mock.AsyncMock,
    ) -> None:
        ctx = cast(Any, Context)(prefix='~', message=MockMessage())

        await ctx.send_embed('baz')

        assert type(mock_context_send.call_args_list[0][1]['embed']) == discord.Embed

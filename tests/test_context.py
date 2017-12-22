import pytest

from erasmus.erasmus import Context
import discord


class MockUser(object):
    __slots__ = ('bot', 'id', 'mention')
    bot: bool
    id: int
    mention: str

    def __init__(self, *, bot: bool = None, id: int = None, mention: str = None) -> None:
        self.bot = bot
        self.id = id
        self.mention = mention


class MockMessage(object):
    __slots__ = ('author', 'content', 'channel', '_state')
    author: MockUser
    content: str
    channel: discord.abc.GuildChannel

    def __init__(self, *, author: MockUser = None, content: str = None) -> None:
        self.author = author
        self.content = content
        self.channel = None
        self._state = None


class TestContext(object):
    @pytest.fixture
    def mock_context_send(self, mocker):
        return mocker.patch('discord.ext.commands.Context.send', new_callable=mocker.AsyncMock)

    @pytest.mark.asyncio
    async def test_send_embed(self, mocker, mock_context_send):
        ctx = Context(prefix='~', message=MockMessage())

        await ctx.send_embed('baz')

        assert type(mock_context_send.call_args_list[0][1]['embed']) == discord.Embed

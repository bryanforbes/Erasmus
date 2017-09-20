import pytest

from erasmus.erasmus import Erasmus, Context
from erasmus.data import SearchResults, Passage # noqa
from erasmus.exceptions import BibleNotSupportedError # noqa


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
    __slots__ = ('author', 'content', '_state')
    author: MockUser
    content: str

    def __init__(self, *, author: MockUser = None, content: str = None) -> None:
        self.author = author
        self.content = content
        self._state = None


class MockCommand(object):
    __slots__ = ('name',)
    name: str

    def __init__(self, name: str) -> None:
        self.name = name


class MockContext(object):
    __slots__ = ('command',)
    command: MockCommand

    def __init__(self, command: MockCommand) -> None:
        self.command = command


class TestContext(object):
    @pytest.fixture
    def mock_context_send(self, mocker):
        return mocker.patch('discord.ext.commands.Context.send', new_callable=mocker.AsyncMock)

    @pytest.mark.asyncio
    async def test_send(self, mocker, mock_context_send):
        ctx = Context(prefix='~', message=MockMessage(author=MockUser(mention='user1')))

        await ctx.send_to_author('baz')

        assert mock_context_send.call_args_list == [
            mocker.call('user1\n```baz```')
        ]


class TestErasmus(object):
    @pytest.fixture(autouse=True)
    def mock_discord_py(self, mocker):
        mocker.patch('discord.ext.commands.Bot.add_command')
        mocker.patch('discord.ext.commands.Bot.run')
        mocker.patch('discord.ext.commands.Bot.invoke', new_callable=mocker.AsyncMock)

    @pytest.fixture
    def mock_send_to_author(self, mocker):
        return mocker.patch('erasmus.erasmus.Context.send_to_author', new_callable=mocker.AsyncMock)

    @pytest.fixture(autouse=True)
    def mock_load(self, mocker):
        mock = mocker.mock_open(read_data='{ "foo": { "bar": "baz" }, "spam": "ham" }')
        mocker.patch('erasmus.erasmus.open', mock)
        return mocker.patch('erasmus.erasmus.load')

    @pytest.fixture(autouse=True)
    def mock_biblemanager(self, mocker):
        mocker.patch('erasmus.erasmus.BibleManager.__init__', autospec=True, return_value=None)
        mocker.patch('erasmus.erasmus.BibleManager.get_versions', return_value=[
            ('esv', 'English Standard Version'),
            ('nasb', 'New American Standard Bible')
        ])
        mocker.patch('erasmus.erasmus.BibleManager.get_passage', new_callable=mocker.AsyncMock)
        mocker.patch('erasmus.erasmus.BibleManager.search', new_callable=mocker.AsyncMock)

    def test_init(self, mocker, mock_load):
        bot = Erasmus('foo/bar/baz.json')

        assert bot.command_prefix == mock_load.return_value.command_prefix
        assert bot.add_command.call_count == 6
        assert bot.add_command.call_args_list[1][0][0].name == 'esv'
        assert bot.add_command.call_args_list[1][0][0].callback == bot._version_lookup
        assert bot.add_command.call_args_list[2][0][0].name == 'sesv'
        assert bot.add_command.call_args_list[2][0][0].callback == bot._version_search
        assert bot.add_command.call_args_list[3][0][0].name == 'nasb'
        assert bot.add_command.call_args_list[3][0][0].callback == bot._version_lookup
        assert bot.add_command.call_args_list[4][0][0].name == 'snasb'
        assert bot.add_command.call_args_list[4][0][0].callback == bot._version_search
        assert bot.add_command.call_args_list[5] == mocker.call(bot.versions)

    # @pytest.mark.asyncio
    # async def test_on_message(self, mocker, mock_send_to_author):
    #     bot = Erasmus('foo/bar/baz.json', command_prefix='~')

    #     bot_message = MockMessage(author=MockUser(bot=True))
    #     message = MockMessage(author=MockUser(bot=False), content='')

    #     await bot.on_message(bot_message)
    #     await bot.on_message(message)

    #     assert bot.invoke.call_args_list == [
    #         mocker.call(message)
    #     ]

    # @pytest.mark.asyncio
    # async def test_versions(self, mock_send_to_author):
    #     bot = Erasmus('foo/bar/baz.json', command_prefix='~')

    #     await bot.versions.callback(bot)

    #     expected = '''
# I support the following Bible versions:
#
#   ~esv:   English Standard Version
#   ~nasb:  New American Standard Bible
#
# You can search any version by prefixing the version command with 's' (ex. ~sesv terms...)
# '''

    #     mock_send.assert_called_once_with(expected)

    # @pytest.mark.asyncio
    # @pytest.mark.usefixtures('mock_say')
    # async def test__version_lookup(self):
    #     bot = Erasmus('foo/bar/baz.json', command_prefix='~')
    #     ctx = MockContext(MockCommand('esv'))

    # @pytest.mark.asyncio
    # async def test__version_search(self, mocker):
    #     bot = Erasmus('foo/bar/baz.json', command_prefix='~')
    #     ctx = MockContext(MockCommand('sesv'))

    #     bot.bible_manager.search.return_value = SearchResults([
    #         Passage.from_string('John 1:1-4')
    #     ], 1)

    #     await bot._version_search(ctx, 'one', 'two', 'three')

    #     bot.bible_manager.search.return_value = SearchResults([
    #         Passage.from_string('John 1:1-4'),
    #         Passage.from_string('Genesis 50:1')
    #     ], 50)

    #     await bot._version_search(ctx, 'three', 'four', 'five')

    #     bot.bible_manager.search.side_effect = BibleNotSupportedError('esv')

    #     await bot._version_search(ctx, 'six', 'seven')

    #     assert bot.type.call_count == 3
    #     assert bot.say.call_args_list == [
    #         mocker.call('I have found 1 match to your search:\nJohn 1:1-4'),
    #         mocker.call('I have found 50 matches to your search. Here are the first 20 matches:\n'
    #                     'John 1:1-4, Genesis 50:1'),
    #         mocker.call('~sesv is not supported')
    #     ]

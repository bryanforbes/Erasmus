import pytest

from erasmus.erasmus import Erasmus
from erasmus.data import SearchResults, Passage
from erasmus.exceptions import BibleNotSupportedError


class MockUser(object):
    __slots__ = ('bot',)
    bot: bool

    def __init__(self, bot: bool) -> None:
        self.bot = bot


class MockMessage(object):
    __slots__ = ('author',)
    author: MockUser

    def __init__(self, author: MockUser) -> None:
        self.author = author


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


class TestErasmus(object):
    @pytest.fixture(autouse=True)
    def mock_discord_py(self, mocker):
        mocker.patch('discord.ext.commands.Bot.__init__', autospec=True, return_value=None)
        mocker.patch('discord.ext.commands.Bot.add_command')
        mocker.patch('discord.ext.commands.Bot.run')
        mocker.patch('discord.ext.commands.Bot.process_commands', new_callable=mocker.AsyncMock)
        mocker.patch('discord.ext.commands.Bot.type', new_callable=mocker.AsyncMock)

    @pytest.fixture
    def mock_bot_say(self, mocker):
        return mocker.patch('discord.ext.commands.Bot.say', new_callable=mocker.AsyncMock)

    @pytest.fixture
    def mock_say(self, mocker):
        return mocker.patch('erasmus.erasmus.Erasmus.say', new_callable=mocker.AsyncMock)

    @pytest.fixture(autouse=True)
    def mock_load(self, mocker):
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

    def test_init(self, mocker):
        bot = Erasmus('foo/bar/baz.json', command_prefix='~')

        assert bot.add_command.call_count == 5
        assert bot.add_command.call_args_list[0][0][0].name == 'esv'
        assert bot.add_command.call_args_list[0][0][0].callback == bot._version_lookup
        assert bot.add_command.call_args_list[1][0][0].name == 'sesv'
        assert bot.add_command.call_args_list[1][0][0].callback == bot._version_search
        assert bot.add_command.call_args_list[2][0][0].name == 'nasb'
        assert bot.add_command.call_args_list[2][0][0].callback == bot._version_lookup
        assert bot.add_command.call_args_list[3][0][0].name == 'snasb'
        assert bot.add_command.call_args_list[3][0][0].callback == bot._version_search
        assert bot.add_command.call_args_list[4] == mocker.call(bot.versions)

    @pytest.mark.asyncio
    async def test_say(self, mocker, mock_bot_say):
        bot = Erasmus('foo/bar/baz.json', command_prefix='~')

        await bot.say(blah='baz')
        await bot.say(content='foo bar baz')
        await bot.say(content='foo bar baz', plain_text=True, blah='baz')

        assert mock_bot_say.call_args_list == [
            mocker.call(None, blah='baz'),
            mocker.call('```foo bar baz```'),
            mocker.call('foo bar baz', blah='baz')
        ]

    @pytest.mark.asyncio
    async def test_on_message(self, mocker):
        bot = Erasmus('foo/bar/baz.json', command_prefix='~')

        bot_message = MockMessage(MockUser(True))
        message = MockMessage(MockUser(False))

        await bot.on_message(bot_message)
        await bot.on_message(message)

        assert bot.process_commands.call_args_list == [
            mocker.call(message)
        ]

    @pytest.mark.asyncio
    @pytest.mark.usefixtures('mock_say')
    async def test_versions(self):
        bot = Erasmus('foo/bar/baz.json', command_prefix='~')

        await bot.versions.callback(bot)

        expected = '''
I support the following Bible versions:

  ~esv:   English Standard Version
  ~nasb:  New American Standard Bible

You can search any version by prefixing the version command with 's' (ex. ~sesv [terms...])
'''

        bot.say.assert_called_once_with(expected)

    # @pytest.mark.asyncio
    # @pytest.mark.usefixtures('mock_say')
    # async def test__version_lookup(self):
    #     bot = Erasmus('foo/bar/baz.json', command_prefix='~')
    #     ctx = MockContext(MockCommand('esv'))

    @pytest.mark.asyncio
    @pytest.mark.usefixtures('mock_say')
    async def test__version_search(self, mocker):
        bot = Erasmus('foo/bar/baz.json', command_prefix='~')
        ctx = MockContext(MockCommand('sesv'))

        bot.bible_manager.search.return_value = SearchResults([
            Passage.from_string('John 1:1-4')
        ], 1)

        await bot._version_search(ctx, 'one', 'two', 'three')

        bot.bible_manager.search.return_value = SearchResults([
            Passage.from_string('John 1:1-4'),
            Passage.from_string('Genesis 50:1')
        ], 50)

        await bot._version_search(ctx, 'three', 'four', 'five')

        bot.bible_manager.search.side_effect = BibleNotSupportedError('esv')

        await bot._version_search(ctx, 'six', 'seven')

        assert bot.type.call_count == 3
        assert bot.say.call_args_list == [
            mocker.call('I have found 1 match to your search:\nJohn 1:1-4'),
            mocker.call('I have found 50 matches to your search. Here are the first 20 matches:\n'
                        'John 1:1-4, Genesis 50:1'),
            mocker.call('~sesv is not supported')
        ]

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import discord
import pytest
from attr import define
from discord import app_commands

from erasmus import utils
from erasmus.data import Passage, VerseRange

if TYPE_CHECKING:
    from unittest.mock import AsyncMock

    from .types import MockerFixture


@pytest.fixture
def mock_send_embed(mocker: MockerFixture) -> AsyncMock:
    return mocker.patch(
        'botus_receptus.utils.send_embed',
        return_value=mocker.sentinel.send_embed_return,
        new_callable=mocker.AsyncMock,
    )


@pytest.mark.parametrize(
    'passage,kwargs,expected_kwargs',
    [
        (
            Passage(
                '**10.** For as many as are of the works of the law are under the '
                'curse: for it is written, Cursed _is_ every one that continueth '
                'not in all things which are written in the book of the law to do '
                'them. **11.** But that no man is justified by the law in the '
                'sight of God, _it is_ evident: for, The just shall live by faith.',
                VerseRange.from_string('Gal 3:10-11'),
                'KJV',
            ),
            {},
            {
                'description': (
                    '**10.** For as many as are of the works of the law are under the '
                    'curse: for it is written, Cursed _is_ every one that continueth '
                    'not in all things which are written in the book of the law to do '
                    'them. **11.** But that no man is justified by the law in the '
                    'sight of God, _it is_ evident: for, The just shall live by faith.'
                ),
                'footer': {'text': 'Galatians 3:10-11 (KJV)'},
            },
        ),
        (
            Passage(
                'a' * 4096,
                VerseRange.from_string('Gen 3:10-11'),
                'ESV',
            ),
            {'ephemeral': True},
            {
                'description': 'a' * 4096,
                'footer': {'text': 'Genesis 3:10-11 (ESV)'},
                'ephemeral': True,
            },
        ),
        (
            Passage(
                'a' * 4097,
                VerseRange.from_string('Gen 3:10-11'),
                'ESV',
            ),
            {'ephemeral': True, 'title': 'A title'},
            {
                'description': '**The passage was too long and has been truncated:'
                f'**\n\n{"a" * 4041}'
                '\u2026',
                'footer': {'text': 'Genesis 3:10-11 (ESV)'},
                'ephemeral': True,
                'title': 'A title',
            },
        ),
    ],
)
async def test_send_passage(
    mocker: MockerFixture,
    mock_send_embed: AsyncMock,
    passage: Passage,
    kwargs: dict[str, Any],
    expected_kwargs: dict[str, object],
) -> None:
    result: discord.Message = await utils.send_passage(
        mocker.sentinel.ctx_or_intx, passage, **kwargs
    )

    assert result is mocker.sentinel.send_embed_return
    mock_send_embed.assert_awaited_once_with(
        mocker.sentinel.ctx_or_intx, **expected_kwargs
    )


@define
class MockOption:
    key: str
    name: str

    def matches(self, text: str, /) -> bool:
        return text in self.name.lower() or text in self.key.lower()

    def choice(self) -> app_commands.Choice[str]:
        return app_commands.Choice(name=self.name, value=self.key)


class TestAutoCompleter:
    def test_init(self) -> None:
        completer: utils.AutoCompleter[MockOption] = utils.AutoCompleter()
        assert completer is not None

    def test_add(self) -> None:
        completer: utils.AutoCompleter[MockOption] = utils.AutoCompleter()

        option1 = MockOption(key='1', name='Test 1')
        option2 = MockOption(key='2', name='Test 2')

        completer.add(option1)
        completer.add(option2)

        assert completer.generate_choices('') == [
            app_commands.Choice(name='Test 1', value='1'),
            app_commands.Choice(name='Test 2', value='2'),
        ]

    def test_update(self) -> None:
        completer: utils.AutoCompleter[MockOption] = utils.AutoCompleter()

        option1 = MockOption(key='1', name='Test 1')
        option2 = MockOption(key='2', name='Test 2')

        completer.update([option1, option2])

        assert completer.generate_choices('') == [
            app_commands.Choice(name='Test 1', value='1'),
            app_commands.Choice(name='Test 2', value='2'),
        ]

    def test_clear(self) -> None:
        completer: utils.AutoCompleter[MockOption] = utils.AutoCompleter()

        option1 = MockOption(key='1', name='Test 1')
        option2 = MockOption(key='2', name='Test 2')

        completer.update([option1, option2])

        completer.clear()

        assert completer.generate_choices('') == []

    def test_discard(self) -> None:
        completer: utils.AutoCompleter[MockOption] = utils.AutoCompleter()

        option1 = MockOption(key='1', name='Test 1')
        option2 = MockOption(key='2', name='Test 2')

        completer.update([option1, option2])

        completer.discard('1')
        completer.discard('3')

        assert completer.generate_choices('') == [
            app_commands.Choice(name='Test 2', value='2'),
        ]

    def test_remove(self) -> None:
        completer: utils.AutoCompleter[MockOption] = utils.AutoCompleter()

        option1 = MockOption(key='1', name='Test 1')
        option2 = MockOption(key='2', name='Test 2')

        completer.update([option1, option2])

        completer.remove('1')

        with pytest.raises(KeyError):
            completer.remove('3')

        assert completer.generate_choices('') == [
            app_commands.Choice(name='Test 2', value='2'),
        ]

    def test_generate_choices(self) -> None:
        completer: utils.AutoCompleter[MockOption] = utils.AutoCompleter()

        option1 = MockOption(key='1', name='Testing 1')
        option2 = MockOption(key='2', name='Tester 2')

        completer.add(option1)
        completer.add(option2)

        assert completer.generate_choices('') == [
            app_commands.Choice(name='Testing 1', value='1'),
            app_commands.Choice(name='Tester 2', value='2'),
        ]

        assert completer.generate_choices(' Testing ') == [
            app_commands.Choice(name='Testing 1', value='1'),
        ]

        completer.update(MockOption(name=f'Testing {x}', key=str(x)) for x in range(50))

        choices = completer.generate_choices(' Testing ')
        assert len(choices) == 25

    async def test_autocomplete(self) -> None:
        completer: utils.AutoCompleter[MockOption] = utils.AutoCompleter()

        option1 = MockOption(key='1', name='Testing 1')
        option2 = MockOption(key='2', name='Tester 2')

        completer.add(option1)
        completer.add(option2)

        assert (await completer.autocomplete(cast('Any', object()), ' Testing ')) == [
            app_commands.Choice(name='Testing 1', value='1'),
        ]

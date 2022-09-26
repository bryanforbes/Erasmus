from __future__ import annotations

import discord
import pytest

from erasmus.cogs.bible.verse_of_the_day_group import TimeTransformer
from erasmus.exceptions import InvalidTimeError


class TestTimeTransformer:
    @pytest.fixture
    def mock_interaction(self) -> object:
        return object()

    @pytest.mark.parametrize(
        'input,expected',
        [
            ('12:00', (12, 0)),
            ('12:15', (12, 15)),
            ('12:00 am', (0, 0)),
            ('1:00', (1, 0)),
            ('1:00 am', (1, 0)),
            ('01:00 am', (1, 0)),
            ('1:00 pm', (13, 0)),
            ('01:00 pm', (13, 0)),
            ('12:00 pm', (12, 0)),
            ('00:59', (0, 59)),
            ('23:48', (23, 48)),
            ('12          :      00', (12, 0)),
            ('           12      :         00           pm        ', (12, 0)),
        ],
    )
    async def test_transform(
        self,
        mock_interaction: discord.Interaction,
        input: str,
        expected: tuple[int, int],
    ) -> None:
        transformer = TimeTransformer()
        assert await transformer.transform(mock_interaction, input) == expected

    @pytest.mark.parametrize(
        'input',
        [
            '13:00 am',
            '13:00 pm',
            '23:00 pm',
            '43:28',
            '00:28 pm',
            '00:67',
            'asdf',
        ],
    )
    async def test_transform_raises(
        self,
        mock_interaction: discord.Interaction,
        input: str,
    ) -> None:
        transformer = TimeTransformer()
        with pytest.raises(InvalidTimeError):
            await transformer.transform(mock_interaction, input)

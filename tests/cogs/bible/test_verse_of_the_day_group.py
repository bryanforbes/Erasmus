from __future__ import annotations

import discord
import pytest

from erasmus.cogs.bible.verse_of_the_day_group import _TimeTransformer
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
            ('1:00am', (1, 0)),
            ('01:00 am', (1, 0)),
            ('1:00 pm', (13, 0)),
            ('01:00 pm', (13, 0)),
            ('12:00 pm', (12, 0)),
            ('1:05', (1, 15)),
            ('1:25', (1, 30)),
            ('1:35', (1, 45)),
            ('1:55', (2, 0)),
            ('00:59', (1, 0)),
            ('23:48', (0, 0)),
            ('11:48 pm', (0, 0)),
            ('12          :      00', (12, 0)),
            ('23          :      18', (23, 30)),
            ('           12      :         00           pm        ', (12, 0)),
        ],
    )
    async def test_transform(
        self,
        mock_interaction: discord.Interaction,
        input: str,
        expected: tuple[int, int],
    ) -> None:
        transformer = _TimeTransformer()
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
        transformer = _TimeTransformer()
        with pytest.raises(InvalidTimeError):
            await transformer.transform(mock_interaction, input)

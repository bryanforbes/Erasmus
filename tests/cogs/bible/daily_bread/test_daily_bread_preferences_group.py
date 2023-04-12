from __future__ import annotations

from typing import TYPE_CHECKING

import pendulum
import pytest

from erasmus.cogs.bible.daily_bread.daily_bread_preferences_group import (
    _TimeTransformer,
)
from erasmus.exceptions import InvalidTimeError

if TYPE_CHECKING:
    import discord


class TestTimeTransformer:
    @pytest.fixture
    def mock_interaction(self) -> object:
        return object()

    @pytest.mark.parametrize(
        'input,expected',
        [
            ('12:00', pendulum.Time(12, 0)),
            ('12:15', pendulum.Time(12, 15)),
            ('12:00 am', pendulum.Time(0, 0)),
            ('1:00', pendulum.Time(1, 0)),
            ('1:00am', pendulum.Time(1, 0)),
            ('01:00 am', pendulum.Time(1, 0)),
            ('1:00 pm', pendulum.Time(13, 0)),
            ('01:00 pm', pendulum.Time(13, 0)),
            ('12:00 pm', pendulum.Time(12, 0)),
            ('1:05', pendulum.Time(1, 15)),
            ('1:25', pendulum.Time(1, 30)),
            ('1:35', pendulum.Time(1, 45)),
            ('1:55', pendulum.Time(2, 0)),
            ('00:59', pendulum.Time(1, 0)),
            ('23:48', pendulum.Time(0, 0)),
            ('11:48 pm', pendulum.Time(0, 0)),
            ('12          :      00', pendulum.Time(12, 0)),
            ('23          :      18', pendulum.Time(23, 30)),
            (
                '           12      :         00           pm        ',
                pendulum.Time(12, 0),
            ),
        ],
    )
    async def test_transform(
        self,
        mock_interaction: discord.Interaction,
        input: str,
        expected: pendulum.Time,
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

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import discord
import pytest
import pytest_mock

from erasmus import utils
from erasmus.data import Passage, VerseRange


@pytest.fixture
def mock_send_embed(mocker: pytest_mock.MockerFixture) -> AsyncMock:
    return mocker.patch(
        'botus_receptus.utils.send_embed',
        return_value=mocker.sentinel.send_embed_return,
    )


@pytest.mark.parametrize(
    'passage,kwargs,description,footer,ephemeral',
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
            '**10.** For as many as are of the works of the law are under the '
            'curse: for it is written, Cursed _is_ every one that continueth '
            'not in all things which are written in the book of the law to do '
            'them. **11.** But that no man is justified by the law in the '
            'sight of God, _it is_ evident: for, The just shall live by faith.',
            'Galatians 3:10-11 (KJV)',
            discord.utils.MISSING,
        ),
        (
            Passage(
                'a' * 4096,
                VerseRange.from_string('Gen 3:10-11'),
                'ESV',
            ),
            {'ephemeral': True},
            'a' * 4096,
            'Genesis 3:10-11 (ESV)',
            True,
        ),
        (
            Passage(
                'a' * 4097,
                VerseRange.from_string('Gen 3:10-11'),
                'ESV',
            ),
            {'ephemeral': True},
            f'**The passage was too long and has been truncated:**\n\n{"a" * 4041}'
            '\u2026',
            'Genesis 3:10-11 (ESV)',
            True,
        ),
    ],
)
@pytest.mark.asyncio
async def test_send_passage(
    mocker: pytest_mock.MockerFixture,
    mock_send_embed: AsyncMock,
    passage: Passage,
    kwargs: dict[str, Any],
    description: str,
    footer: str,
    ephemeral: Any,
) -> None:
    result = await utils.send_passage(mocker.sentinel.ctx_or_intx, passage, **kwargs)

    assert result is mocker.sentinel.send_embed_return
    mock_send_embed.assert_awaited_once_with(
        mocker.sentinel.ctx_or_intx,
        description=description,
        footer={'text': footer},
        ephemeral=ephemeral,
    )
from __future__ import annotations

import pytest

from erasmus.cogs.confession import Confession
from erasmus.erasmus import Erasmus
from erasmus.l10n import Localizer


class MockBot(object):
    ...


class MockLocalizer(object):
    ...


class TestConfession(object):
    @pytest.fixture
    def mock_bot(self) -> MockBot:
        return MockBot()

    @pytest.fixture
    def mock_localizer(self) -> MockLocalizer:
        return MockLocalizer()

    def test_instantiate(self, mock_bot: Erasmus, mock_localizer: Localizer) -> None:
        cog = Confession(mock_bot, mock_localizer)
        assert cog is not None

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from erasmus.cogs.confession import Confession, ConfessionAppCommands
from erasmus.types import Refreshable

if TYPE_CHECKING:
    from erasmus.erasmus import Erasmus


class MockBot:
    localizer = object()


@pytest.fixture
def mock_bot() -> MockBot:
    return MockBot()


class TestConfession:
    def test_instantiate(self, mock_bot: Erasmus) -> None:
        cog = Confession(mock_bot)
        assert cog is not None
        assert not isinstance(cog, Refreshable)


class TestConfessionAppCommands:
    def test_instantiate(self, mock_bot: Erasmus) -> None:
        cog = ConfessionAppCommands(mock_bot)
        assert cog is not None
        assert isinstance(cog, Refreshable)

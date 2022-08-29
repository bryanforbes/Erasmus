from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from erasmus.cogs.confession import Confession
from erasmus.types import Refreshable

if TYPE_CHECKING:
    from erasmus.erasmus import Erasmus


class MockBot:
    localizer = object()


class TestConfession:
    @pytest.fixture
    def mock_bot(self) -> MockBot:
        return MockBot()

    def test_instantiate(self, mock_bot: Erasmus) -> None:
        cog = Confession(mock_bot)
        assert cog is not None
        assert isinstance(cog, Refreshable)

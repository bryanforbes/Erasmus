from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from erasmus.cogs.confession import Confession

if TYPE_CHECKING:
    from erasmus.erasmus import Erasmus


class MockBot:
    ...


class TestConfession:
    @pytest.fixture
    def mock_bot(self) -> MockBot:
        return MockBot()

    def test_instantiate(self, mock_bot: Erasmus) -> None:
        cog = Confession(mock_bot)
        assert cog is not None

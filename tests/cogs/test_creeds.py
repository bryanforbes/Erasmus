from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from erasmus.cogs.creeds import Creeds

if TYPE_CHECKING:
    from erasmus.erasmus import Erasmus


class MockBot(object):
    ...


class TestCreeds(object):
    @pytest.fixture
    def mock_bot(self) -> MockBot:
        return MockBot()

    def test_instantiate(self, mock_bot: Erasmus) -> None:
        cog = Creeds(mock_bot)
        assert cog is not None

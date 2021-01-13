from __future__ import annotations

from typing import Any

import pytest

from erasmus.cogs.bible import Bible
from erasmus.erasmus import Erasmus


class MockBot(object):
    config: Any = {}
    session: Any = {}


class TestBible(object):
    @pytest.fixture
    def mock_bot(self) -> MockBot:
        return MockBot()

    def test_instantiate(self, mock_bot: Erasmus) -> None:
        cog = Bible(mock_bot)
        assert cog is not None

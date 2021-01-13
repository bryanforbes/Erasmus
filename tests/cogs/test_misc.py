from __future__ import annotations

import pytest

from erasmus.cogs.misc import Misc
from erasmus.erasmus import Erasmus


class MockBot(object):
    ...


class TestMisc(object):
    @pytest.fixture
    def mock_bot(self) -> MockBot:
        return MockBot()

    def test_instantiate(self, mock_bot: Erasmus) -> None:
        cog = Misc(mock_bot)
        assert cog is not None

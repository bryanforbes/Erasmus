import pytest

from erasmus.cogs.confession import Confession
from erasmus.erasmus import Erasmus


class MockBot(object):
    ...


class TestConfession(object):
    @pytest.fixture
    def mock_bot(self) -> MockBot:
        return MockBot()

    def test_instantiate(self, mock_bot: Erasmus) -> None:
        cog = Confession(mock_bot)
        assert cog is not None

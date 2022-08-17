from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from erasmus.cogs.misc import Misc

if TYPE_CHECKING:
    from erasmus.erasmus import Erasmus


class MockBot(object):
    localizer = object()


class TestMisc(object):
    @pytest.fixture
    def mock_bot(self) -> MockBot:
        return MockBot()

    def test_instantiate(self, mock_bot: Erasmus) -> None:
        cog = Misc(mock_bot)
        assert cog is not None

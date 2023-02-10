from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from erasmus.cogs.bible.cog import Bible
from erasmus.types import Refreshable

if TYPE_CHECKING:
    from unittest.mock import Mock

    from erasmus.erasmus import Erasmus

    from ...types import MockerFixture


class TestBible:
    @pytest.fixture
    def mock_bot(self, mocker: MockerFixture) -> Mock:
        return mocker.Mock()

    def test_instantiate(self, mock_bot: Erasmus) -> None:
        cog = Bible(mock_bot)
        assert cog is not None
        assert isinstance(cog, Refreshable)

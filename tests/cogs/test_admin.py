from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import pytest_mock

from erasmus.cogs.admin import Admin
from erasmus.erasmus import Erasmus
from erasmus.types import Refreshable

if TYPE_CHECKING:
    from unittest.mock import Mock


class TestAdmin:
    @pytest.fixture
    def mock_bot(self, mocker: pytest_mock.MockerFixture) -> Mock:
        return mocker.Mock(spec=Erasmus, config={})

    def test_instantiate(self, mock_bot: Mock) -> None:
        cog = Admin(mock_bot)
        assert cog is not None
        assert not isinstance(cog, Refreshable)
        assert not hasattr(cog, '_eval')

    def test_instantiate_with_eval(self, mock_bot: Mock) -> None:
        mock_bot.configure_mock(config={'enable_eval': True})
        cog = Admin(mock_bot)
        assert cog is not None
        assert not isinstance(cog, Refreshable)
        assert hasattr(cog, '_eval')

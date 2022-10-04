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
        return mocker.Mock(spec=Erasmus)

    def test_instantiate(self, mock_bot: Erasmus) -> None:
        cog = Admin(mock_bot)
        assert cog is not None
        assert not isinstance(cog, Refreshable)

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from erasmus.cogs.confession import Confession
from erasmus.erasmus import Erasmus
from erasmus.l10n import Localizer
from erasmus.types import Refreshable

if TYPE_CHECKING:
    from unittest.mock import Mock

    from ..types import MockerFixture


class TestConfession:
    @pytest.fixture
    def mock_bot(self, mocker: MockerFixture) -> Mock:
        localizer = mocker.Mock(spec_set=Localizer)
        return mocker.Mock(spec=Erasmus, localizer=localizer)

    def test_instantiate(self, mock_bot: Erasmus) -> None:
        cog = Confession(mock_bot)
        assert cog is not None
        assert isinstance(cog, Refreshable)

from __future__ import annotations

from typing import Any

import pytest

from erasmus.cogs.bible import Bible
from erasmus.erasmus import Erasmus
from erasmus.service_manager import ServiceManager


class MockBot(object):
    config: Any = {}
    session: Any = {}


class MockServiceManager(object):
    ...


class TestBible(object):
    @pytest.fixture
    def mock_bot(self) -> MockBot:
        return MockBot()

    @pytest.fixture
    def mock_service_manager(self) -> MockServiceManager:
        return MockServiceManager()

    def test_instantiate(
        self, mock_bot: Erasmus, mock_service_manager: ServiceManager
    ) -> None:
        cog = Bible(mock_bot, mock_service_manager)
        assert cog is not None

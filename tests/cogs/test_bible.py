from __future__ import annotations

from unittest.mock import Mock

import pytest
from pytest_mock import MockerFixture

from erasmus.cogs.bible import Bible, BibleAppCommands
from erasmus.erasmus import Erasmus
from erasmus.service_manager import ServiceManager


class MockServiceManager(object):
    ...


@pytest.fixture
def mock_bot(mocker: MockerFixture) -> Mock:
    bot = mocker.Mock()
    bot.config = mocker.Mock()
    bot.session = mocker.Mock()

    return bot


@pytest.fixture
def mock_service_manager() -> MockServiceManager:
    return MockServiceManager()


class TestBible(object):
    def test_instantiate(
        self,
        mock_bot: Erasmus,
        mock_service_manager: ServiceManager,
    ) -> None:
        cog = Bible(mock_bot, mock_service_manager)
        assert cog is not None


class TestBibleAppCommands(object):
    def test_instantiate(
        self,
        mock_bot: Erasmus,
        mock_service_manager: ServiceManager,
    ) -> None:
        cog = BibleAppCommands(mock_bot, mock_service_manager)
        assert cog is not None

from __future__ import annotations

from typing import Any
from unittest.mock import Mock

import pytest
from pytest_mock import MockerFixture

from erasmus.cogs.bible import Bible, BibleAppCommands
from erasmus.erasmus import Erasmus
from erasmus.l10n import Localizer
from erasmus.service_manager import ServiceManager


class MockBot(object):
    config: Any = {}
    session: Any = {}


class MockServiceManager(object):
    ...


class MockLocalizer(object):
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


@pytest.fixture
def mock_localizer() -> MockLocalizer:
    return MockLocalizer()


class TestBible(object):
    def test_instantiate(
        self,
        mock_bot: Erasmus,
        mock_service_manager: ServiceManager,
        mock_localizer: Localizer,
    ) -> None:
        cog = Bible(mock_bot, mock_service_manager, mock_localizer)
        assert cog is not None


class TestBibleAppCommands(object):
    def test_instantiate(
        self,
        mock_bot: Erasmus,
        mock_service_manager: ServiceManager,
        mock_localizer: Localizer,
    ) -> None:
        cog = BibleAppCommands(mock_bot, mock_service_manager, mock_localizer)
        assert cog is not None

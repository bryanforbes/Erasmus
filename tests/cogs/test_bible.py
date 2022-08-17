from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from erasmus.cogs.bible import Bible, BibleAppCommands

if TYPE_CHECKING:
    from unittest.mock import Mock

    from pytest_mock import MockerFixture

    from erasmus.erasmus import Erasmus
    from erasmus.service_manager import ServiceManager


class MockServiceManager:
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


class TestBible:
    def test_instantiate(
        self,
        mock_bot: Erasmus,
        mock_service_manager: ServiceManager,
    ) -> None:
        cog = Bible(mock_bot, mock_service_manager)
        assert cog is not None


class TestBibleAppCommands:
    def test_instantiate(
        self,
        mock_bot: Erasmus,
        mock_service_manager: ServiceManager,
    ) -> None:
        cog = BibleAppCommands(mock_bot, mock_service_manager)
        assert cog is not None

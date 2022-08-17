from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import aiohttp
import pytest
import pytest_mock
from attrs import define

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from unittest.mock import MagicMock


@pytest.fixture(scope='session', autouse=True)
def vcr_config() -> dict[str, list[str]]:
    return {'filter_headers': ['authorization', 'api-key']}


@define
class MockBible(object):
    command: str
    name: str
    abbr: str
    service: str
    service_version: str
    rtl: bool = False


@pytest.fixture(name='MockBible', scope='session')
def fixture_MockBible() -> type[MockBible]:
    return MockBible


@pytest.fixture
def mock_response(mocker: pytest_mock.MockerFixture) -> MagicMock:
    response = mocker.MagicMock()
    cast('Any', response).__aenter__.return_value = response

    return response


@pytest.fixture
def mock_client_session(
    mocker: pytest_mock.MockerFixture, mock_response: Any
) -> MagicMock:
    session: MagicMock = mocker.MagicMock()
    cast('Any', session).__aenter__.return_value = session
    session.get = mocker.Mock(return_value=mock_response)
    session.post = mocker.Mock(return_value=mock_response)

    return session


@pytest.fixture
async def aiohttp_client_session(
    event_loop: Any,
) -> AsyncIterator[aiohttp.ClientSession]:
    async with aiohttp.ClientSession(loop=event_loop) as session:
        yield session


@pytest.fixture
def mock_aiohttp(
    mocker: pytest_mock.MockerFixture, mock_client_session: MagicMock
) -> None:
    ClientSession = mocker.Mock()
    ClientSession.return_value = mock_client_session
    mocker.patch('aiohttp.ClientSession', return_value=ClientSession)

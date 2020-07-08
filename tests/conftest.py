from __future__ import annotations

from typing import Any

import asynctest.mock  # type: ignore
import pytest  # type: ignore
import pytest_mock  # type: ignore
from attr import dataclass

pytest_mock._get_mock_module._module = asynctest.mock


@dataclass(slots=True)
class MockBible(object):
    command: str
    name: str
    abbr: str
    service: str
    service_version: str
    rtl: bool = False


@pytest.fixture(name='MockBible', scope='session')
def fixture_MockBible() -> None:
    return MockBible


@pytest.fixture
def mock_response(mocker: Any) -> None:
    response = mocker.MagicMock()
    response.__aenter__.return_value = response

    return response


@pytest.fixture
def mock_client_session(mocker: Any, mock_response: Any) -> None:
    session = mocker.MagicMock()
    session.__aenter__.return_value = session
    session.get = mocker.Mock(return_value=mock_response)
    session.post = mocker.Mock(return_value=mock_response)

    return session


@pytest.fixture
def mock_aiohttp(mocker: Any, mock_client_session) -> None:
    ClientSession = mocker.Mock()
    ClientSession.return_value = mock_client_session
    mocker.patch('aiohttp.ClientSession', return_value=ClientSession)


@pytest.fixture(autouse=True)
def add_async_mocks(mocker: Any) -> None:
    mocker.CoroutineMock = mocker.mock_module.CoroutineMock

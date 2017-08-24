import pytest
import aiohttp
import asyncio
from unittest.mock import Mock

def AsyncMock(*args, **kwargs):
    mock = Mock(*args, **kwargs)

    _type = type(mock)

    async def call_mock(*args, **kwargs):
        return Mock.__call__(mock, *args, **kwargs)

    setattr(_type, '__call__', call_mock)

    return mock

def AsyncWithMock(*args, **kwargs):
    mock = Mock(*args, **kwargs)

    _type = type(mock)

    setattr(_type, '__aenter__', AsyncMock())

    def exit(*args, **kwargs):
        pass

    setattr(_type, '__aexit__', AsyncMock(side_effect=exit))

    return mock

@pytest.fixture(autouse=True)
def add_async_mocks(mocker):
    mocker.AsyncMock = AsyncMock
    mocker.AsyncWithMock = AsyncWithMock

@pytest.fixture
def mock_response(mocker):
    response = mocker.AsyncWithMock()
    response.__aenter__.return_value = response

    return response

@pytest.fixture
def mock_client_session(mocker):
    session = mocker.AsyncWithMock()
    session.__aenter__.return_value = session

    return session

@pytest.fixture
def MockClientSession(mocker, mock_client_session, mock_response):
    mocker.patch.object(mock_client_session, 'get', return_value=mock_response)

    ClientSession = mocker.Mock()
    ClientSession.return_value = mock_client_session

    return ClientSession

@pytest.fixture(autouse=True)
def aiohttp(mocker, MockClientSession):
    mocker.patch('aiohttp.ClientSession', MockClientSession)

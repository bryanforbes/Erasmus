import pytest
import aiohttp
import asyncio
from unittest.mock import Mock

class AsyncMock(Mock):
    async def __call__(_mock_self, *args, **kwargs):
        _mock_self._mock_check_sig(*args, **kwargs)
        return _mock_self._mock_call(*args, **kwargs)

def AsyncWithMock(*args, **kwargs):
    mock = Mock(*args, **kwargs)

    def exit(*args, **kwargs):
        pass

    setattr(type(mock), '__aenter__', AsyncMock())
    setattr(type(mock), '__aexit__', AsyncMock(side_effect=exit))

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

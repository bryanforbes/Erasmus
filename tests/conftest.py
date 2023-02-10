from __future__ import annotations

from typing import TYPE_CHECKING, Any

import aiohttp
import pytest
from attrs import define

from .utils import create_async_context_manager

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from unittest.mock import MagicMock, Mock

    from .types import MockerFixture


@pytest.fixture(scope='session', autouse=True)
def vcr_config() -> dict[str, list[str]]:
    return {'filter_headers': ['authorization', 'api-key']}


@define
class MockBible:
    command: str
    name: str
    abbr: str
    service: str
    service_version: str
    rtl: bool = False
    book_mapping: dict[str, str] | None = None


@pytest.fixture(name='MockBible', scope='session')
def fixture_MockBible() -> type[MockBible]:
    return MockBible


@pytest.fixture
def mock_get_response(mocker: MockerFixture) -> Mock:
    return mocker.Mock(
        text=mocker.AsyncMock(return_value=mocker.sentinel.get_response_text)
    )


@pytest.fixture
def mock_post_response(mocker: MockerFixture) -> Mock:
    return mocker.Mock(
        text=mocker.AsyncMock(return_value=mocker.sentinel.post_response_text)
    )


@pytest.fixture
def mock_client_session(
    mocker: MockerFixture, mock_get_response: Mock, mock_post_response: Mock
) -> MagicMock:
    return mocker.MagicMock(
        **{
            'get.return_value': create_async_context_manager(mocker, mock_get_response),
            'post.return_value': create_async_context_manager(
                mocker, mock_post_response
            ),
        }
    )


@pytest.fixture
async def aiohttp_client_session(
    event_loop: Any,
) -> AsyncIterator[aiohttp.ClientSession]:
    async with aiohttp.ClientSession(loop=event_loop) as session:
        yield session


@pytest.fixture
def mock_aiohttp(mocker: MockerFixture, mock_client_session: MagicMock) -> None:
    ClientSession = mocker.Mock()
    ClientSession.return_value = mock_client_session
    mocker.patch('aiohttp.ClientSession', return_value=ClientSession)

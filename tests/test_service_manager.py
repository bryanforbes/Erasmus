from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, cast

import aiohttp
import pytest
import pytest_mock

from erasmus.data import Passage, SearchResults, VerseRange
from erasmus.exceptions import ServiceLookupTimeout, ServiceSearchTimeout
from erasmus.service_manager import ServiceManager

if TYPE_CHECKING:
    from erasmus.types import Bible, Service


class MockService:
    __slots__ = 'get_passage', 'search'

    def __init__(self, mocker: pytest_mock.MockerFixture) -> None:
        self.get_passage = mocker.AsyncMock()
        self.search = mocker.AsyncMock()


class MockBible:
    __slots__ = (
        'command',
        'name',
        'abbr',
        'service',
        'service_version',
        'rtl',
        'books',
        'book_mapping',
    )

    def __init__(
        self,
        *,
        command: str,
        name: str,
        abbr: str,
        service: str,
        service_version: str,
        rtl: bool | None = False,
    ) -> None:
        self.command = command
        self.name = name
        self.abbr = abbr
        self.service = service
        self.service_version = service_version
        self.rtl = rtl
        self.books = 1
        self.book_mapping = None


class TestServiceManager:
    @pytest.fixture(autouse=True)
    def services(self, mocker: pytest_mock.MockerFixture) -> dict[str, Any]:
        services = {
            '__all__': ['ServiceOne', 'ServiceTwo'],
            'ServiceOne': mocker.Mock(
                **{'from_config.return_value': mocker.sentinel.SERVICE_ONE}
            ),
            'ServiceTwo': mocker.Mock(
                **{'from_config.return_value': mocker.sentinel.SERVICE_TWO}
            ),
        }

        mocker.patch.dict(
            cast('Any', 'erasmus.services.__dict__'), services, clear=True
        )

        return services

    @pytest.fixture
    def service_one(self, mocker: pytest_mock.MockerFixture) -> Service:
        return MockService(mocker)

    @pytest.fixture
    def service_two(self, mocker: pytest_mock.MockerFixture) -> Service:
        return MockService(mocker)

    @pytest.fixture
    def config(self) -> Any:
        return {'services': {'ServiceTwo': {'api_key': 'foo bar baz'}}}

    @pytest.fixture
    def bible1(self) -> Bible:
        return MockBible(
            command='bible1',
            name='Bible 1',
            abbr='BIB1',
            service='ServiceOne',
            service_version='service-BIB1',
        )

    @pytest.fixture
    def bible2(self) -> Bible:
        return MockBible(
            command='bible2',
            name='Bible 2',
            abbr='BIB2',
            service='ServiceTwo',
            service_version='service-BIB2',
        )

    def test_from_config(
        self,
        mocker: pytest_mock.MockerFixture,
        services: dict[str, Any],
        config: Any,
        mock_client_session: aiohttp.ClientSession,
    ) -> None:
        manager = ServiceManager.from_config(config, mock_client_session)

        services['ServiceOne'].from_config.assert_called_once_with(
            None, mock_client_session
        )
        services['ServiceTwo'].from_config.assert_called_once_with(
            config['services']['ServiceTwo'], mock_client_session
        )
        assert manager.service_map['ServiceOne'] == mocker.sentinel.SERVICE_ONE
        assert manager.service_map['ServiceTwo'] == mocker.sentinel.SERVICE_TWO

    def test_container_methods(
        self, config: Any, mock_client_session: aiohttp.ClientSession
    ) -> None:
        manager = ServiceManager.from_config(config, mock_client_session)

        assert 'ServiceOne' in manager
        assert 'ServiceTwo' in manager
        assert '__all__' not in manager
        assert len(manager) == 2

    async def test_get_passage(
        self,
        bible2: Bible,
        service_one: MockService,
        service_two: MockService,
    ) -> None:
        manager = ServiceManager({'ServiceOne': service_one, 'ServiceTwo': service_two})
        service_one.get_passage.return_value = Passage(
            'blah', VerseRange.from_string('Genesis 2:2'), version='BIB1'
        )
        service_two.get_passage.return_value = Passage(
            'blah', VerseRange.from_string('Genesis 1:2'), version='BIB2'
        )

        result = await manager.get_passage(
            bible2, VerseRange.from_string('Genesis 1:2')
        )

        assert result == Passage('blah', VerseRange.from_string('Genesis 1:2'), 'BIB2')
        service_two.get_passage.assert_called_once_with(
            bible2, VerseRange.from_string('Genesis 1:2')
        )

    async def test_get_passage_timeout(
        self,
        bible1: Bible,
        service_one: MockService,
        service_two: MockService,
    ) -> None:
        async def get_passage(*args: Any, **kwargs: Any) -> None:
            await asyncio.sleep(0.5)

        manager = ServiceManager(
            {'ServiceOne': service_one, 'ServiceTwo': service_two}, timeout=0.1
        )
        service_one.get_passage.side_effect = get_passage

        with pytest.raises(ServiceLookupTimeout) as exc_info:
            await manager.get_passage(bible1, VerseRange.from_string('Genesis 1:2'))

        assert exc_info.value.bible == bible1
        assert exc_info.value.verses == VerseRange.from_string('Genesis 1:2')

    async def test_search(
        self,
        bible1: Bible,
        service_one: MockService,
        service_two: MockService,
    ) -> None:
        manager = ServiceManager({'ServiceOne': service_one, 'ServiceTwo': service_two})
        service_one.search.return_value = SearchResults(verses=[], total=10)
        service_two.search.return_value = SearchResults(verses=[], total=20)

        result = await manager.search(
            bible1, ['one', 'two', 'three'], limit=10, offset=20
        )
        assert result == SearchResults(verses=[], total=10)
        service_one.search.assert_called_once_with(
            bible1, ['one', 'two', 'three'], limit=10, offset=20
        )

    async def test_search_timeout(
        self,
        bible1: Bible,
        service_one: MockService,
        service_two: MockService,
    ) -> None:
        async def search(*args: Any, **kwargs: Any) -> None:
            await asyncio.sleep(0.5)

        manager = ServiceManager(
            {'ServiceOne': service_one, 'ServiceTwo': service_two}, timeout=0.1
        )
        service_one.search.side_effect = search

        with pytest.raises(ServiceSearchTimeout) as exc_info:
            await manager.search(bible1, ['one', 'two', 'three'])

        assert exc_info.value.bible == bible1
        assert exc_info.value.terms == ['one', 'two', 'three']

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import aiohttp
import discord
import pytest

from erasmus.cogs.bible.daily_bread.daily_bread_group import (
    DailyBreadGroup,
    PassageFetcher,
)
from erasmus.data import SectionFlag, VerseRange
from erasmus.exceptions import (
    BookNotInVersionError,
    DoNotUnderstandError,
    ServiceNotSupportedError,
)
from erasmus.service_manager import ServiceManager
from erasmus.utils import frozen

if TYPE_CHECKING:
    from collections.abc import Iterator
    from unittest.mock import AsyncMock, Mock, NonCallableMock

    from pytest_mock import MockerFixture

    from erasmus.types import Bible


@frozen
class MockBible:
    id: int
    command: str
    name: str
    abbr: str
    service: str
    service_version: str
    rtl: bool | None = False
    books: SectionFlag = SectionFlag.OT | SectionFlag.NT
    book_mapping: dict[str, str] | None = None


@pytest.fixture
def mock_service_manager(mocker: MockerFixture) -> Mock:
    return mocker.create_autospec(ServiceManager)


@pytest.fixture
def bible1() -> Bible:
    return MockBible(
        id=1,
        command='bible1',
        name='Bible 1',
        abbr='BIB1',
        service='ServiceOne',
        service_version='service-BIB1',
    )


@pytest.fixture
def bible2() -> Bible:
    return MockBible(
        id=2,
        command='bible2',
        name='Bible 2',
        abbr='BIB2',
        service='ServiceTwo',
        service_version='service-BIB2',
        books=SectionFlag.OT,
    )


class TestPassageFetcher:
    def test_init(self, mock_service_manager: Mock) -> None:
        fetcher = PassageFetcher(
            VerseRange.from_string('Genesis 1:2'), mock_service_manager
        )

        assert fetcher.verse_range == VerseRange.from_string('Genesis 1:2')
        assert fetcher.service_manager is mock_service_manager
        assert fetcher.passage_map == {}

    async def test_call(
        self,
        mocker: MockerFixture,
        mock_service_manager: Mock,
        bible1: Bible,
        bible2: Bible,
    ) -> None:
        mock_service_manager.configure_mock(
            **{'get_passage.return_value': mocker.sentinel.get_passage_return}
        )
        fetcher = PassageFetcher(
            VerseRange.from_string('Genesis 1:2'), mock_service_manager
        )

        assert (await fetcher(bible2)) is mocker.sentinel.get_passage_return
        assert (await fetcher(bible1)) is mocker.sentinel.get_passage_return

        mock_service_manager.get_passage.assert_has_awaits(  # type: ignore
            [
                mocker.call(bible2, VerseRange.from_string('Genesis 1:2')),
                mocker.call(bible1, VerseRange.from_string('Genesis 1:2')),
            ]
        )

    async def test_call_cached(
        self,
        mocker: MockerFixture,
        mock_service_manager: Mock,
        bible1: Bible,
        bible2: Bible,
    ) -> None:
        mock_service_manager.configure_mock(
            **{'get_passage.return_value': mocker.sentinel.get_passage_return}
        )
        fetcher = PassageFetcher(
            VerseRange.from_string('Genesis 1:2'), mock_service_manager
        )

        await fetcher(bible2)
        await fetcher(bible1)

        mock_service_manager.get_passage.reset_mock()  # type: ignore

        assert (await fetcher(bible2)) is mocker.sentinel.get_passage_return
        assert (await fetcher(bible1)) is mocker.sentinel.get_passage_return

        mock_service_manager.get_passage.assert_not_awaited()  # type: ignore


class TestDailyBreadGroup:
    @pytest.fixture
    def mock_passage_fetcher(self, mocker: MockerFixture) -> AsyncMock:
        return mocker.AsyncMock(
            return_value=mocker.sentinel.passage,
            verse_range=mocker.sentinel.passage_verse_range,
        )

    @pytest.fixture
    def mock_daily_bread(self, mocker: MockerFixture) -> NonCallableMock:
        return mocker.NonCallableMock(
            guild_id=42,
            url='daily_bread_url',
            next_scheduled=mocker.sentinel.daily_bread_next_scheduled,
            time=mocker.sentinel.daily_bread_time,
            timezone=mocker.sentinel.daily_bread_timezone,
            prefs=None,
        )

    @pytest.fixture
    def mock_send_passage(self, mocker: MockerFixture) -> AsyncMock:
        return mocker.patch(
            'erasmus.cogs.bible.daily_bread.daily_bread_group.send_passage',
            new_callable=mocker.AsyncMock,
        )

    @pytest.fixture
    def mock_db_session(self, mocker: MockerFixture) -> NonCallableMock:
        db_session = mocker.NonCallableMock()
        db_session.attach_mock(mocker.AsyncMock(), 'commit')

        db_session_cm = mocker.NonCallableMock()
        db_session_cm.__aenter__ = mocker.AsyncMock(return_value=db_session)
        db_session_cm.__aexit__ = mocker.AsyncMock(return_value=False)

        mocker.patch(
            'erasmus.cogs.bible.daily_bread.daily_bread_group.Session.begin',
            return_value=db_session_cm,
        )

        return db_session

    @pytest.fixture
    def mock_daily_bread_scheduled(
        self, mocker: MockerFixture, mock_daily_bread: NonCallableMock
    ) -> AsyncMock:
        return mocker.patch(
            'erasmus.cogs.bible.daily_bread.daily_bread_group.DailyBread.scheduled',
            new_callable=mocker.AsyncMock,
            return_value=[mock_daily_bread],
        )

    @pytest.fixture
    def mock_get_next_scheduled_time(self, mocker: MockerFixture) -> Iterator[Mock]:
        mock = mocker.patch(
            'erasmus.cogs.bible.daily_bread.daily_bread_group.get_next_scheduled_time',
            return_value=mocker.sentinel.next_scheduled_time,
        )

        yield mock

        mock.assert_called_once_with(
            mocker.sentinel.daily_bread_next_scheduled,
            mocker.sentinel.daily_bread_time,
            mocker.sentinel.daily_bread_timezone,
        )

    @pytest.fixture
    def mock_bible_version_get_by_command(
        self, mocker: MockerFixture, bible1: MockBible
    ) -> AsyncMock:
        return mocker.patch(
            'erasmus.cogs.bible.daily_bread.daily_bread_group.BibleVersion.'
            'get_by_command',
            new_callable=mocker.AsyncMock,
            return_value=bible1,
        )

    @pytest.fixture
    def mock_webhook_from_url(self, mocker: MockerFixture) -> Iterator[Mock]:
        mock = mocker.patch(
            'discord.Webhook.from_url', return_value=mocker.sentinel.webhook
        )

        yield mock

        mock.assert_called_once_with(
            'https://discord.com/api/webhooks/daily_bread_url',
            session=mocker.sentinel.client_session,
        )

    @pytest.fixture
    def daily_bread_group(
        self,
        mock_service_manager: Mock,
    ) -> DailyBreadGroup:
        group = DailyBreadGroup()
        group._fetcher = None
        group.service_manager = mock_service_manager
        return group

    @pytest.fixture
    def daily_bread_group_with_session_sentinel(
        self, mocker: MockerFixture, daily_bread_group: DailyBreadGroup
    ) -> DailyBreadGroup:
        daily_bread_group.session = mocker.sentinel.client_session  # pyright: ignore
        return daily_bread_group

    @pytest.mark.vcr
    async def test_get_verse_range(self, daily_bread_group: DailyBreadGroup) -> None:
        daily_bread_group.session = aiohttp.ClientSession()
        assert (await daily_bread_group._get_verse_range()) == VerseRange.from_string(
            '2 Thessalonians 1:3'
        )

    async def test_get_verse_range_raises(
        self,
        mocker: MockerFixture,
        daily_bread_group: DailyBreadGroup,
    ) -> None:
        mock_response_text = mocker.AsyncMock(return_value='<html></html>')

        mock_response = mocker.NonCallableMock()
        mock_response.attach_mock(mock_response_text, 'text')

        mock_response_cm = mocker.MagicMock()
        mock_response_cm.__aenter__ = mocker.AsyncMock(return_value=mock_response)
        mock_response_cm.__aexit__ = mocker.AsyncMock(return_value=False)

        mock_session_get = mocker.Mock(return_value=mock_response_cm)

        mock_session = mocker.NonCallableMock()
        mock_session.attach_mock(mock_session_get, 'get')

        daily_bread_group.session = mock_session

        with pytest.raises(DoNotUnderstandError):
            await daily_bread_group._get_verse_range()

    def test_get_fetcher(self, daily_bread_group: DailyBreadGroup) -> None:
        verse_range = VerseRange.from_string('John 1:1-15')

        fetcher1 = daily_bread_group._get_fetcher(verse_range)
        fetcher2 = daily_bread_group._get_fetcher(verse_range)

        assert isinstance(fetcher1, PassageFetcher)
        assert fetcher1 is fetcher2

        fetcher3 = daily_bread_group._get_fetcher(VerseRange.from_string('Genesis 1:2'))

        assert fetcher3 is not fetcher1

    @pytest.mark.parametrize('thread_id', [1, None])
    async def test_fetch_and_post(
        self,
        mocker: MockerFixture,
        daily_bread_group: DailyBreadGroup,
        thread_id: int | None,
        bible1: Bible,
        mock_passage_fetcher: AsyncMock,
        mock_daily_bread: NonCallableMock,
        mock_send_passage: AsyncMock,
    ) -> None:
        mock_daily_bread.thread_id = thread_id

        assert await daily_bread_group._fetch_and_post(
            mock_passage_fetcher,
            mock_daily_bread,
            bible1,  # pyright: ignore
            mocker.sentinel.webhook,  # pyright: ignore
        )

        mock_passage_fetcher.assert_awaited_once_with(bible1)
        mock_send_passage.assert_awaited_once_with(
            mocker.sentinel.webhook,
            mocker.sentinel.passage,
            thread=discord.Object(1)
            if thread_id is not None
            else discord.utils.MISSING,
            avatar_url='https://i.imgur.com/XQ8N2vH.png',
        )

    @pytest.mark.parametrize(
        'exception_class',
        [
            DoNotUnderstandError,
            BookNotInVersionError('Genesis', 'KJV'),
            ServiceNotSupportedError(
                MockBible(
                    id=1,
                    command='bible1',
                    name='Bible 1',
                    abbr='BIB1',
                    service='ServiceOne',
                    service_version='service-BIB1',
                )
            ),
        ],
    )
    async def test_fetch_and_post_fetching_raises(
        self,
        mocker: MockerFixture,
        daily_bread_group: DailyBreadGroup,
        exception_class: type[Exception],
        bible1: Bible,
        mock_passage_fetcher: AsyncMock,
        mock_daily_bread: NonCallableMock,
        mock_send_passage: AsyncMock,
    ) -> None:
        mock_passage_fetcher.side_effect = exception_class

        assert await daily_bread_group._fetch_and_post(
            mock_passage_fetcher,
            mock_daily_bread,
            bible1,  # pyright: ignore
            mocker.sentinel.webhook,  # pyright: ignore
        )

        mock_passage_fetcher.assert_awaited_once_with(bible1)
        mock_send_passage.assert_not_awaited()

    @pytest.mark.parametrize(
        'exception_class,code,expected',
        [
            (discord.NotFound, 10015, True),
            (discord.NotFound, 401, False),
            (RuntimeError, None, False),
        ],
    )
    async def test_fetch_and_post_posting_raises(
        self,
        mocker: MockerFixture,
        daily_bread_group: DailyBreadGroup,
        exception_class: type[Exception],
        code: int | None,
        expected: bool,
        bible1: Bible,
        mock_passage_fetcher: AsyncMock,
        mock_daily_bread: NonCallableMock,
        mock_send_passage: AsyncMock,
    ) -> None:
        mock_passage_fetcher.side_effect = (
            exception_class(mocker.MagicMock(), {'code': code, 'errors': {}})
            if code is not None
            else exception_class
        )

        assert (
            await daily_bread_group._fetch_and_post(
                mock_passage_fetcher,
                mock_daily_bread,
                bible1,  # pyright: ignore
                mocker.sentinel.webhook,  # pyright: ignore
            )
        ) == expected

        mock_passage_fetcher.assert_awaited_once_with(bible1)
        mock_send_passage.assert_not_awaited()

    @pytest.mark.usefixtures(
        'mock_bible_version_get_by_command',
        'mock_webhook_from_url',
        'mock_get_next_scheduled_time',
        'daily_bread_group_with_session_sentinel',
    )
    async def test_check_and_post(
        self,
        mocker: MockerFixture,
        daily_bread_group: DailyBreadGroup,
        mock_db_session: NonCallableMock,
        mock_daily_bread_scheduled: AsyncMock,
        mock_daily_bread: NonCallableMock,
        bible1: MockBible,
    ) -> None:
        daily_bread_group._get_verse_range = mocker.AsyncMock(
            return_value=VerseRange.from_string('John 1:1-15')
        )
        daily_bread_group._fetch_and_post = mocker.AsyncMock(return_value=True)

        await daily_bread_group._check_and_post()

        mock_daily_bread_scheduled.assert_awaited_once_with(mock_db_session)
        assert (
            mock_daily_bread.next_scheduled  # pyright: ignore
            is mocker.sentinel.next_scheduled_time
        )
        daily_bread_group._fetch_and_post.assert_awaited_once_with(
            mocker.ANY, mock_daily_bread, bible1, mocker.sentinel.webhook
        )
        mock_db_session.commit.assert_awaited_once_with()  # pyright: ignore

    @pytest.mark.usefixtures(
        'mock_bible_version_get_by_command',
        'mock_webhook_from_url',
        'mock_get_next_scheduled_time',
        'daily_bread_group_with_session_sentinel',
    )
    async def test_check_and_post_with_prefs(
        self,
        mocker: MockerFixture,
        daily_bread_group: DailyBreadGroup,
        mock_db_session: NonCallableMock,
        mock_daily_bread_scheduled: AsyncMock,
        mock_daily_bread: NonCallableMock,
        bible2: MockBible,
    ) -> None:
        mock_daily_bread.prefs = mocker.Mock(bible_version=bible2)
        daily_bread_group._get_verse_range = mocker.AsyncMock(
            return_value=VerseRange.from_string('Genesis 1:1-15')
        )
        daily_bread_group._fetch_and_post = mocker.AsyncMock(return_value=True)

        await daily_bread_group._check_and_post()

        mock_daily_bread_scheduled.assert_awaited_once_with(mock_db_session)
        assert (
            mock_daily_bread.next_scheduled  # pyright: ignore
            is mocker.sentinel.next_scheduled_time
        )
        daily_bread_group._fetch_and_post.assert_awaited_once_with(
            mocker.ANY, mock_daily_bread, bible2, mocker.sentinel.webhook
        )
        mock_db_session.commit.assert_awaited_once_with()  # pyright: ignore

    @pytest.mark.usefixtures(
        'mock_webhook_from_url',
        'mock_get_next_scheduled_time',
        'daily_bread_group_with_session_sentinel',
    )
    async def test_check_and_post_not_in_bible(
        self,
        mocker: MockerFixture,
        daily_bread_group: DailyBreadGroup,
        mock_db_session: NonCallableMock,
        mock_daily_bread_scheduled: AsyncMock,
        mock_daily_bread: NonCallableMock,
        mock_bible_version_get_by_command: AsyncMock,
        bible2: MockBible,
    ) -> None:
        daily_bread_group._get_verse_range = mocker.AsyncMock(
            return_value=VerseRange.from_string('John 1:1-15')
        )
        daily_bread_group._fetch_and_post = mocker.AsyncMock(return_value=True)
        mock_bible_version_get_by_command.return_value = bible2

        await daily_bread_group._check_and_post()

        mock_daily_bread_scheduled.assert_awaited_once_with(mock_db_session)
        assert (
            mock_daily_bread.next_scheduled  # pyright: ignore
            is mocker.sentinel.next_scheduled_time
        )
        daily_bread_group._fetch_and_post.assert_not_awaited()
        mock_db_session.commit.assert_awaited_once_with()  # pyright: ignore

    @pytest.mark.usefixtures(
        'mock_webhook_from_url',
        'mock_get_next_scheduled_time',
        'mock_bible_version_get_by_command',
        'daily_bread_group_with_session_sentinel',
    )
    async def test_check_and_post_next_scheduled_not_set(
        self,
        mocker: MockerFixture,
        daily_bread_group: DailyBreadGroup,
        mock_db_session: NonCallableMock,
        mock_daily_bread_scheduled: AsyncMock,
        mock_daily_bread: NonCallableMock,
        bible1: MockBible,
    ) -> None:
        daily_bread_group._get_verse_range = mocker.AsyncMock(
            return_value=VerseRange.from_string('John 1:1-15')
        )
        daily_bread_group._fetch_and_post = mocker.AsyncMock(return_value=False)

        await daily_bread_group._check_and_post()

        mock_daily_bread_scheduled.assert_awaited_once_with(mock_db_session)
        assert (
            mock_daily_bread.next_scheduled  # pyright: ignore
            is mocker.sentinel.daily_bread_next_scheduled
        )
        daily_bread_group._fetch_and_post.assert_awaited_once_with(
            mocker.ANY, mock_daily_bread, bible1, mocker.sentinel.webhook
        )
        mock_db_session.commit.assert_awaited_once_with()  # pyright: ignore

    async def test_check_and_post_no_daily_bread(
        self,
        daily_bread_group: DailyBreadGroup,
        mock_db_session: NonCallableMock,
        mock_daily_bread_scheduled: AsyncMock,
    ) -> None:
        mock_daily_bread_scheduled.return_value = []

        await daily_bread_group._check_and_post()

        mock_daily_bread_scheduled.assert_awaited_once_with(mock_db_session)
        mock_db_session.commit.assert_not_awaited()  # pyright: ignore

    @pytest.mark.usefixtures('mock_daily_bread_scheduled')
    async def test_check_and_post_fetching_verse_range_raises(
        self,
        mocker: MockerFixture,
        daily_bread_group: DailyBreadGroup,
        mock_db_session: NonCallableMock,
    ) -> None:
        daily_bread_group._get_verse_range = mocker.AsyncMock(
            side_effect=asyncio.TimeoutError
        )
        await daily_bread_group._check_and_post()

        daily_bread_group._get_verse_range.side_effect = DoNotUnderstandError
        await daily_bread_group._check_and_post()

        mock_db_session.commit.assert_not_awaited()  # pyright: ignore

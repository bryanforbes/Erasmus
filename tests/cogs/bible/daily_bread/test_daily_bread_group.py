from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import discord
import pytest
from attrs import evolve, frozen

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

from ....utils import create_async_context_manager

if TYPE_CHECKING:
    from unittest.mock import AsyncMock, MagicMock, Mock, NonCallableMock

    import aiohttp

    from erasmus.types import Bible

    from ....types import MockerFixture


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
def mock_service_manager(mocker: MockerFixture) -> NonCallableMock:
    return mocker.NonCallableMock(
        get_passage=mocker.AsyncMock(
            side_effect=[
                mocker.sentinel.get_passage_return_1,
                mocker.sentinel.get_passage_return_2,
            ]
        ),
    )


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
        books=SectionFlag.NT,
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
        fetcher = PassageFetcher(
            VerseRange.from_string('Genesis 1:2'), mock_service_manager
        )

        assert (await fetcher(bible2)) is mocker.sentinel.get_passage_return_1
        assert (await fetcher(bible1)) is mocker.sentinel.get_passage_return_2

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
        fetcher = PassageFetcher(
            VerseRange.from_string('Genesis 1:2'), mock_service_manager
        )

        await fetcher(bible2)
        await fetcher(bible1)
        assert (await fetcher(bible2)) is mocker.sentinel.get_passage_return_1
        assert (await fetcher(bible1)) is mocker.sentinel.get_passage_return_2

        mock_service_manager.get_passage.assert_has_awaits(  # type: ignore
            [
                mocker.call(bible2, VerseRange.from_string('Genesis 1:2')),
                mocker.call(bible1, VerseRange.from_string('Genesis 1:2')),
            ]
        )


class TestDailyBreadGroup:
    @pytest.fixture
    def mock_daily_bread(self, mocker: MockerFixture) -> NonCallableMock:
        return mocker.NonCallableMock(
            guild_id=42,
            thread_id=84,
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

        db_session_cm = create_async_context_manager(mocker, db_session)

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
    def mock_get_next_scheduled_time(self, mocker: MockerFixture) -> Mock:
        return mocker.patch(
            'erasmus.cogs.bible.daily_bread.daily_bread_group.get_next_scheduled_time',
            side_effect=[
                mocker.sentinel.next_scheduled_time_1,
                mocker.sentinel.next_scheduled_time_2,
            ],
        )

    @pytest.fixture(autouse=True)
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
    def mock_webhook_from_url(self, mocker: MockerFixture) -> Mock:
        return mocker.patch(
            'discord.Webhook.from_url',
            side_effect=[mocker.sentinel.webhook_1, mocker.sentinel.webhook_2],
        )

    @pytest.fixture
    def daily_bread_group(
        self,
        mocker: MockerFixture,
        aiohttp_client_session: aiohttp.ClientSession,
        mock_service_manager: Mock,
    ) -> DailyBreadGroup:
        group = DailyBreadGroup()

        group.initialize_from_parent(
            mocker.NonCallableMock(
                bot=mocker.NonCallableMock(session=aiohttp_client_session),
                service_manager=mock_service_manager,
                localizer=mocker.NonCallableMock(
                    **{'for_group.return_value': mocker.sentinel.group_localizer}
                ),
            )
        )

        return group

    async def test_initialize_from_parent(self, mocker: MockerFixture) -> None:
        group = DailyBreadGroup()
        group.initialize_from_parent(
            mocker.NonCallableMock(
                bot=mocker.NonCallableMock(session=mocker.sentinel.client_session),
                service_manager=mocker.sentinel.service_manager,
                localizer=mocker.NonCallableMock(
                    **{'for_group.return_value': mocker.sentinel.group_localizer}
                ),
            )
        )

        assert group.session is mocker.sentinel.client_session
        assert group.service_manager is mocker.sentinel.service_manager
        assert group.localizer is mocker.sentinel.group_localizer
        assert group._fetcher is None

    @pytest.mark.default_cassette('verse_range.yaml')
    @pytest.mark.vcr
    async def test_check_and_post(
        self,
        mocker: MockerFixture,
        daily_bread_group: DailyBreadGroup,
        mock_db_session: NonCallableMock,
        bible1: MockBible,
        mock_daily_bread_scheduled: AsyncMock,
        mock_service_manager: NonCallableMock,
        mock_get_next_scheduled_time: Mock,
        mock_webhook_from_url: Mock,
        mock_send_passage: AsyncMock,
        mock_daily_bread: NonCallableMock,
    ) -> None:
        await daily_bread_group._check_and_post()

        mock_daily_bread_scheduled.assert_awaited_once_with(mock_db_session)
        mock_get_next_scheduled_time.assert_called_once_with(
            mocker.sentinel.daily_bread_next_scheduled,
            mocker.sentinel.daily_bread_time,
            mocker.sentinel.daily_bread_timezone,
        )
        mock_webhook_from_url.assert_called_once_with(
            'https://discord.com/api/webhooks/daily_bread_url',
            session=daily_bread_group.session,
        )
        mock_service_manager.get_passage.assert_awaited_once_with(  # pyright: ignore
            bible1, VerseRange.from_string('1 Corinthians 13:1-3')
        )
        mock_send_passage.assert_awaited_once_with(
            mocker.sentinel.webhook_1,
            mocker.sentinel.get_passage_return_1,
            thread=discord.Object(84),
            avatar_url='https://i.imgur.com/XQ8N2vH.png',
        )
        assert (
            mock_daily_bread.next_scheduled  # pyright: ignore
            is mocker.sentinel.next_scheduled_time_1
        )
        mock_db_session.commit.assert_awaited_once_with()  # pyright: ignore

    async def test_check_and_post_no_results(
        self,
        daily_bread_group: DailyBreadGroup,
        mock_db_session: NonCallableMock,
        mock_daily_bread_scheduled: AsyncMock,
        mock_service_manager: NonCallableMock,
        mock_get_next_scheduled_time: Mock,
        mock_webhook_from_url: Mock,
        mock_send_passage: AsyncMock,
    ) -> None:
        mock_daily_bread_scheduled.return_value = []

        await daily_bread_group._check_and_post()

        mock_daily_bread_scheduled.assert_awaited_once_with(mock_db_session)
        mock_get_next_scheduled_time.assert_not_called()
        mock_webhook_from_url.assert_not_called()
        mock_service_manager.get_passage.assert_not_awaited()  # pyright: ignore
        mock_send_passage.assert_not_awaited()
        mock_db_session.commit.assert_not_awaited()  # pyright: ignore

    async def test_check_and_post_verse_range_times_out(
        self,
        mocker: MockerFixture,
        daily_bread_group: DailyBreadGroup,
        mock_client_session: MagicMock,
        mock_db_session: NonCallableMock,
        mock_daily_bread_scheduled: AsyncMock,
        mock_service_manager: NonCallableMock,
        mock_get_next_scheduled_time: Mock,
        mock_webhook_from_url: Mock,
        mock_send_passage: AsyncMock,
        mock_daily_bread: NonCallableMock,
    ) -> None:
        daily_bread_group.session = mock_client_session
        mock_client_session.get.side_effect = asyncio.TimeoutError  # pyright: ignore

        await daily_bread_group._check_and_post()

        mock_daily_bread_scheduled.assert_awaited_once_with(mock_db_session)
        mock_get_next_scheduled_time.assert_not_called()
        mock_webhook_from_url.assert_not_called()
        mock_service_manager.get_passage.assert_not_awaited()  # pyright: ignore
        mock_send_passage.assert_not_awaited()
        assert (
            mock_daily_bread.next_scheduled  # pyright: ignore
            is mocker.sentinel.daily_bread_next_scheduled
        )
        mock_db_session.commit.assert_not_awaited()  # pyright: ignore

    async def test_check_and_post_verse_range_invalid(
        self,
        mocker: MockerFixture,
        daily_bread_group: DailyBreadGroup,
        mock_client_session: MagicMock,
        mock_get_response: Mock,
        mock_db_session: NonCallableMock,
        mock_daily_bread_scheduled: AsyncMock,
        mock_service_manager: NonCallableMock,
        mock_get_next_scheduled_time: Mock,
        mock_webhook_from_url: Mock,
        mock_send_passage: AsyncMock,
        mock_daily_bread: NonCallableMock,
    ) -> None:
        daily_bread_group.session = mock_client_session
        mock_get_response.text.return_value = '<html></html>'  # pyright: ignore

        await daily_bread_group._check_and_post()

        mock_daily_bread_scheduled.assert_awaited_once_with(mock_db_session)
        mock_get_next_scheduled_time.assert_not_called()
        mock_webhook_from_url.assert_not_called()
        mock_service_manager.get_passage.assert_not_awaited()  # pyright: ignore
        mock_send_passage.assert_not_awaited()
        assert (
            mock_daily_bread.next_scheduled  # pyright: ignore
            is mocker.sentinel.daily_bread_next_scheduled
        )
        mock_db_session.commit.assert_not_awaited()  # pyright: ignore

    @pytest.mark.default_cassette('verse_range.yaml')
    @pytest.mark.vcr
    async def test_check_and_post_with_prefs(
        self,
        mocker: MockerFixture,
        daily_bread_group: DailyBreadGroup,
        mock_db_session: NonCallableMock,
        bible2: MockBible,
        mock_daily_bread_scheduled: AsyncMock,
        mock_service_manager: NonCallableMock,
        mock_get_next_scheduled_time: Mock,
        mock_webhook_from_url: Mock,
        mock_send_passage: AsyncMock,
        mock_daily_bread: NonCallableMock,
    ) -> None:
        mock_daily_bread.prefs = mocker.Mock(bible_version=bible2)

        await daily_bread_group._check_and_post()

        mock_daily_bread_scheduled.assert_awaited_once_with(mock_db_session)
        mock_get_next_scheduled_time.assert_called_once_with(
            mocker.sentinel.daily_bread_next_scheduled,
            mocker.sentinel.daily_bread_time,
            mocker.sentinel.daily_bread_timezone,
        )
        mock_webhook_from_url.assert_called_once_with(
            'https://discord.com/api/webhooks/daily_bread_url',
            session=daily_bread_group.session,
        )
        mock_service_manager.get_passage.assert_awaited_once_with(  # pyright: ignore
            bible2, VerseRange.from_string('1 Corinthians 13:1-3')
        )
        mock_send_passage.assert_awaited_once_with(
            mocker.sentinel.webhook_1,
            mocker.sentinel.get_passage_return_1,
            thread=discord.Object(84),
            avatar_url='https://i.imgur.com/XQ8N2vH.png',
        )
        assert (
            mock_daily_bread.next_scheduled  # pyright: ignore
            is mocker.sentinel.next_scheduled_time_1
        )
        mock_db_session.commit.assert_awaited_once_with()  # pyright: ignore

    @pytest.mark.default_cassette('verse_range.yaml')
    @pytest.mark.vcr
    async def test_check_and_post_not_in_bible(
        self,
        mocker: MockerFixture,
        daily_bread_group: DailyBreadGroup,
        mock_db_session: NonCallableMock,
        bible2: MockBible,
        mock_daily_bread_scheduled: AsyncMock,
        mock_service_manager: NonCallableMock,
        mock_get_next_scheduled_time: Mock,
        mock_webhook_from_url: Mock,
        mock_send_passage: AsyncMock,
        mock_daily_bread: NonCallableMock,
    ) -> None:
        mock_daily_bread.prefs = mocker.Mock(
            bible_version=evolve(bible2, books=SectionFlag.OT)
        )
        await daily_bread_group._check_and_post()

        mock_daily_bread_scheduled.assert_awaited_once_with(mock_db_session)
        mock_get_next_scheduled_time.assert_called_once_with(
            mocker.sentinel.daily_bread_next_scheduled,
            mocker.sentinel.daily_bread_time,
            mocker.sentinel.daily_bread_timezone,
        )
        mock_webhook_from_url.assert_called_once_with(
            'https://discord.com/api/webhooks/daily_bread_url',
            session=daily_bread_group.session,
        )
        mock_service_manager.get_passage.assert_not_awaited()  # pyright: ignore
        mock_send_passage.assert_not_awaited()
        assert (
            mock_daily_bread.next_scheduled  # pyright: ignore
            is mocker.sentinel.next_scheduled_time_1
        )
        mock_db_session.commit.assert_awaited_once_with()  # pyright: ignore

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
    @pytest.mark.default_cassette('verse_range.yaml')
    @pytest.mark.vcr
    async def test_check_and_post_get_passage_raises(
        self,
        mocker: MockerFixture,
        daily_bread_group: DailyBreadGroup,
        exception_class: type[Exception],
        mock_db_session: NonCallableMock,
        bible1: MockBible,
        mock_daily_bread_scheduled: AsyncMock,
        mock_service_manager: NonCallableMock,
        mock_get_next_scheduled_time: Mock,
        mock_webhook_from_url: Mock,
        mock_send_passage: AsyncMock,
        mock_daily_bread: NonCallableMock,
    ) -> None:
        mock_service_manager.get_passage.side_effect = (  # pyright: ignore
            exception_class
        )

        await daily_bread_group._check_and_post()

        mock_daily_bread_scheduled.assert_awaited_once_with(mock_db_session)
        mock_get_next_scheduled_time.assert_called_once_with(
            mocker.sentinel.daily_bread_next_scheduled,
            mocker.sentinel.daily_bread_time,
            mocker.sentinel.daily_bread_timezone,
        )
        mock_webhook_from_url.assert_called_once_with(
            'https://discord.com/api/webhooks/daily_bread_url',
            session=daily_bread_group.session,
        )
        mock_service_manager.get_passage.assert_awaited_once_with(  # pyright: ignore
            bible1, VerseRange.from_string('1 Corinthians 13:1-3')
        )
        mock_send_passage.assert_not_awaited()
        assert (
            mock_daily_bread.next_scheduled  # pyright: ignore
            is mocker.sentinel.next_scheduled_time_1
        )
        mock_db_session.commit.assert_awaited_once_with()  # pyright: ignore

    @pytest.mark.parametrize(
        'exception_class,code,expected_to_set',
        [
            (discord.NotFound, 10015, True),
            (discord.NotFound, 401, False),
            (RuntimeError, None, False),
        ],
    )
    @pytest.mark.default_cassette('verse_range.yaml')
    @pytest.mark.vcr
    async def test_check_and_post_send_passage_raises(
        self,
        mocker: MockerFixture,
        daily_bread_group: DailyBreadGroup,
        exception_class: type[Exception],
        code: int | None,
        expected_to_set: bool,
        mock_db_session: NonCallableMock,
        bible1: MockBible,
        mock_daily_bread_scheduled: AsyncMock,
        mock_service_manager: NonCallableMock,
        mock_get_next_scheduled_time: Mock,
        mock_webhook_from_url: Mock,
        mock_send_passage: AsyncMock,
        mock_daily_bread: NonCallableMock,
    ) -> None:
        mock_send_passage.side_effect = (
            exception_class(mocker.MagicMock(), {'code': code, 'errors': {}})
            if code is not None
            else exception_class
        )

        await daily_bread_group._check_and_post()

        mock_daily_bread_scheduled.assert_awaited_once_with(mock_db_session)
        mock_get_next_scheduled_time.assert_called_once_with(
            mocker.sentinel.daily_bread_next_scheduled,
            mocker.sentinel.daily_bread_time,
            mocker.sentinel.daily_bread_timezone,
        )
        mock_webhook_from_url.assert_called_once_with(
            'https://discord.com/api/webhooks/daily_bread_url',
            session=daily_bread_group.session,
        )
        mock_service_manager.get_passage.assert_awaited_once_with(  # pyright: ignore
            bible1, VerseRange.from_string('1 Corinthians 13:1-3')
        )
        mock_send_passage.assert_awaited_once_with(
            mocker.sentinel.webhook_1,
            mocker.sentinel.get_passage_return_1,
            thread=discord.Object(84),
            avatar_url='https://i.imgur.com/XQ8N2vH.png',
        )
        assert mock_daily_bread.next_scheduled is (  # pyright: ignore
            mocker.sentinel.next_scheduled_time_1
            if expected_to_set
            else mocker.sentinel.daily_bread_next_scheduled
        )
        mock_db_session.commit.assert_awaited_once_with()  # pyright: ignore

    @pytest.mark.default_cassette('verse_range.yaml')
    @pytest.mark.vcr
    async def test_check_and_post_two_with_same_bible(
        self,
        mocker: MockerFixture,
        daily_bread_group: DailyBreadGroup,
        mock_db_session: NonCallableMock,
        bible1: MockBible,
        mock_daily_bread_scheduled: AsyncMock,
        mock_service_manager: NonCallableMock,
        mock_get_next_scheduled_time: Mock,
        mock_webhook_from_url: Mock,
        mock_send_passage: AsyncMock,
        mock_daily_bread: NonCallableMock,
    ) -> None:
        mock_daily_bread_2 = mocker.NonCallableMock(
            guild_id=142,
            thread_id=None,
            url='daily_bread_url_2',
            next_scheduled=mocker.sentinel.daily_bread_next_scheduled_2,
            time=mocker.sentinel.daily_bread_time_2,
            timezone=mocker.sentinel.daily_bread_timezone_2,
            prefs=mocker.Mock(bible_version=bible1),
        )
        mock_daily_bread_scheduled.return_value = [
            mock_daily_bread,
            mock_daily_bread_2,
        ]

        await daily_bread_group._check_and_post()

        mock_daily_bread_scheduled.assert_awaited_once_with(mock_db_session)
        mock_get_next_scheduled_time.assert_has_calls(
            [
                mocker.call(
                    mocker.sentinel.daily_bread_next_scheduled,
                    mocker.sentinel.daily_bread_time,
                    mocker.sentinel.daily_bread_timezone,
                ),
                mocker.call(
                    mocker.sentinel.daily_bread_next_scheduled_2,
                    mocker.sentinel.daily_bread_time_2,
                    mocker.sentinel.daily_bread_timezone_2,
                ),
            ]
        )
        mock_webhook_from_url.assert_has_calls(
            [
                mocker.call(
                    'https://discord.com/api/webhooks/daily_bread_url',
                    session=daily_bread_group.session,
                ),
                mocker.call(
                    'https://discord.com/api/webhooks/daily_bread_url_2',
                    session=daily_bread_group.session,
                ),
            ]
        )
        mock_service_manager.get_passage.assert_awaited_once_with(  # pyright: ignore
            bible1, VerseRange.from_string('1 Corinthians 13:1-3')
        )
        mock_send_passage.assert_has_awaits(
            [
                mocker.call(
                    mocker.sentinel.webhook_1,
                    mocker.sentinel.get_passage_return_1,
                    thread=discord.Object(84),
                    avatar_url='https://i.imgur.com/XQ8N2vH.png',
                ),
                mocker.call(
                    mocker.sentinel.webhook_2,
                    mocker.sentinel.get_passage_return_1,
                    thread=discord.utils.MISSING,
                    avatar_url='https://i.imgur.com/XQ8N2vH.png',
                ),
            ]
        )
        assert (
            mock_daily_bread.next_scheduled  # pyright: ignore
            is mocker.sentinel.next_scheduled_time_1
        )
        assert (
            mock_daily_bread_2.next_scheduled  # pyright: ignore
            is mocker.sentinel.next_scheduled_time_2
        )
        mock_db_session.commit.assert_awaited_once_with()  # pyright: ignore

    @pytest.mark.default_cassette('verse_range_twice.yaml')
    @pytest.mark.vcr
    async def test_check_and_post_twice_with_same_bible(
        self,
        mocker: MockerFixture,
        daily_bread_group: DailyBreadGroup,
        mock_db_session: NonCallableMock,
        bible1: MockBible,
        mock_daily_bread_scheduled: AsyncMock,
        mock_service_manager: NonCallableMock,
        mock_get_next_scheduled_time: Mock,
        mock_webhook_from_url: Mock,
        mock_send_passage: AsyncMock,
        mock_daily_bread: NonCallableMock,
    ) -> None:
        mock_daily_bread_2 = mocker.NonCallableMock(
            guild_id=142,
            thread_id=None,
            url='daily_bread_url_2',
            next_scheduled=mocker.sentinel.daily_bread_next_scheduled_2,
            time=mocker.sentinel.daily_bread_time_2,
            timezone=mocker.sentinel.daily_bread_timezone_2,
            prefs=mocker.Mock(bible_version=bible1),
        )
        mock_daily_bread_scheduled.side_effect = [
            [mock_daily_bread],
            [mock_daily_bread_2],
        ]

        await daily_bread_group._check_and_post()
        await daily_bread_group._check_and_post()

        mock_daily_bread_scheduled.assert_has_awaits(
            [
                mocker.call(mock_db_session),
                mocker.call(mock_db_session),
            ]
        )
        mock_get_next_scheduled_time.assert_has_calls(
            [
                mocker.call(
                    mocker.sentinel.daily_bread_next_scheduled,
                    mocker.sentinel.daily_bread_time,
                    mocker.sentinel.daily_bread_timezone,
                ),
                mocker.call(
                    mocker.sentinel.daily_bread_next_scheduled_2,
                    mocker.sentinel.daily_bread_time_2,
                    mocker.sentinel.daily_bread_timezone_2,
                ),
            ]
        )
        mock_webhook_from_url.assert_has_calls(
            [
                mocker.call(
                    'https://discord.com/api/webhooks/daily_bread_url',
                    session=daily_bread_group.session,
                ),
                mocker.call(
                    'https://discord.com/api/webhooks/daily_bread_url_2',
                    session=daily_bread_group.session,
                ),
            ]
        )
        mock_service_manager.get_passage.assert_awaited_once_with(  # pyright: ignore
            bible1, VerseRange.from_string('1 Corinthians 13:1-3')
        )
        mock_send_passage.assert_has_awaits(
            [
                mocker.call(
                    mocker.sentinel.webhook_1,
                    mocker.sentinel.get_passage_return_1,
                    thread=discord.Object(84),
                    avatar_url='https://i.imgur.com/XQ8N2vH.png',
                ),
                mocker.call(
                    mocker.sentinel.webhook_2,
                    mocker.sentinel.get_passage_return_1,
                    thread=discord.utils.MISSING,
                    avatar_url='https://i.imgur.com/XQ8N2vH.png',
                ),
            ]
        )
        assert (
            mock_daily_bread.next_scheduled  # pyright: ignore
            is mocker.sentinel.next_scheduled_time_1
        )
        assert (
            mock_daily_bread_2.next_scheduled  # pyright: ignore
            is mocker.sentinel.next_scheduled_time_2
        )
        mock_db_session.commit.assert_has_awaits(  # pyright: ignore
            [mocker.call(), mocker.call()]
        )

    @pytest.mark.default_cassette('verse_range.yaml')
    @pytest.mark.vcr
    async def test_check_and_post_two_with_different_bible(
        self,
        mocker: MockerFixture,
        daily_bread_group: DailyBreadGroup,
        mock_db_session: NonCallableMock,
        bible1: MockBible,
        bible2: MockBible,
        mock_daily_bread_scheduled: AsyncMock,
        mock_service_manager: NonCallableMock,
        mock_get_next_scheduled_time: Mock,
        mock_webhook_from_url: Mock,
        mock_send_passage: AsyncMock,
        mock_daily_bread: NonCallableMock,
    ) -> None:
        mock_daily_bread_2 = mocker.NonCallableMock(
            guild_id=142,
            thread_id=None,
            url='daily_bread_url_2',
            next_scheduled=mocker.sentinel.daily_bread_next_scheduled_2,
            time=mocker.sentinel.daily_bread_time_2,
            timezone=mocker.sentinel.daily_bread_timezone_2,
            prefs=mocker.Mock(bible_version=bible2),
        )
        mock_daily_bread_scheduled.return_value = [
            mock_daily_bread,
            mock_daily_bread_2,
        ]

        await daily_bread_group._check_and_post()

        mock_daily_bread_scheduled.assert_awaited_once_with(mock_db_session)
        mock_get_next_scheduled_time.assert_has_calls(
            [
                mocker.call(
                    mocker.sentinel.daily_bread_next_scheduled,
                    mocker.sentinel.daily_bread_time,
                    mocker.sentinel.daily_bread_timezone,
                ),
                mocker.call(
                    mocker.sentinel.daily_bread_next_scheduled_2,
                    mocker.sentinel.daily_bread_time_2,
                    mocker.sentinel.daily_bread_timezone_2,
                ),
            ]
        )
        mock_webhook_from_url.assert_has_calls(
            [
                mocker.call(
                    'https://discord.com/api/webhooks/daily_bread_url',
                    session=daily_bread_group.session,
                ),
                mocker.call(
                    'https://discord.com/api/webhooks/daily_bread_url_2',
                    session=daily_bread_group.session,
                ),
            ]
        )
        mock_service_manager.get_passage.assert_has_awaits(  # pyright: ignore
            [
                mocker.call(bible1, VerseRange.from_string('1 Corinthians 13:1-3')),
                mocker.call(bible2, VerseRange.from_string('1 Corinthians 13:1-3')),
            ]
        )
        mock_send_passage.assert_has_awaits(
            [
                mocker.call(
                    mocker.sentinel.webhook_1,
                    mocker.sentinel.get_passage_return_1,
                    thread=discord.Object(84),
                    avatar_url='https://i.imgur.com/XQ8N2vH.png',
                ),
                mocker.call(
                    mocker.sentinel.webhook_2,
                    mocker.sentinel.get_passage_return_2,
                    thread=discord.utils.MISSING,
                    avatar_url='https://i.imgur.com/XQ8N2vH.png',
                ),
            ]
        )
        assert (
            mock_daily_bread.next_scheduled  # pyright: ignore
            is mocker.sentinel.next_scheduled_time_1
        )
        assert (
            mock_daily_bread_2.next_scheduled  # pyright: ignore
            is mocker.sentinel.next_scheduled_time_2
        )
        mock_db_session.commit.assert_awaited_once_with()  # pyright: ignore

    @pytest.mark.default_cassette('verse_range_twice.yaml')
    @pytest.mark.vcr
    async def test_check_and_post_twice_with_different_bible(
        self,
        mocker: MockerFixture,
        daily_bread_group: DailyBreadGroup,
        mock_db_session: NonCallableMock,
        bible1: MockBible,
        bible2: MockBible,
        mock_daily_bread_scheduled: AsyncMock,
        mock_service_manager: NonCallableMock,
        mock_get_next_scheduled_time: Mock,
        mock_webhook_from_url: Mock,
        mock_send_passage: AsyncMock,
        mock_daily_bread: NonCallableMock,
    ) -> None:
        mock_daily_bread_2 = mocker.NonCallableMock(
            guild_id=142,
            thread_id=None,
            url='daily_bread_url_2',
            next_scheduled=mocker.sentinel.daily_bread_next_scheduled_2,
            time=mocker.sentinel.daily_bread_time_2,
            timezone=mocker.sentinel.daily_bread_timezone_2,
            prefs=mocker.Mock(bible_version=bible2),
        )
        mock_daily_bread_scheduled.side_effect = [
            [mock_daily_bread],
            [mock_daily_bread_2],
        ]

        await daily_bread_group._check_and_post()
        await daily_bread_group._check_and_post()

        mock_daily_bread_scheduled.assert_has_awaits(
            [
                mocker.call(mock_db_session),
                mocker.call(mock_db_session),
            ]
        )
        mock_get_next_scheduled_time.assert_has_calls(
            [
                mocker.call(
                    mocker.sentinel.daily_bread_next_scheduled,
                    mocker.sentinel.daily_bread_time,
                    mocker.sentinel.daily_bread_timezone,
                ),
                mocker.call(
                    mocker.sentinel.daily_bread_next_scheduled_2,
                    mocker.sentinel.daily_bread_time_2,
                    mocker.sentinel.daily_bread_timezone_2,
                ),
            ]
        )
        mock_webhook_from_url.assert_has_calls(
            [
                mocker.call(
                    'https://discord.com/api/webhooks/daily_bread_url',
                    session=daily_bread_group.session,
                ),
                mocker.call(
                    'https://discord.com/api/webhooks/daily_bread_url_2',
                    session=daily_bread_group.session,
                ),
            ]
        )
        mock_service_manager.get_passage.assert_has_awaits(  # pyright: ignore
            [
                mocker.call(bible1, VerseRange.from_string('1 Corinthians 13:1-3')),
                mocker.call(bible2, VerseRange.from_string('1 Corinthians 13:1-3')),
            ]
        )
        mock_send_passage.assert_has_awaits(
            [
                mocker.call(
                    mocker.sentinel.webhook_1,
                    mocker.sentinel.get_passage_return_1,
                    thread=discord.Object(84),
                    avatar_url='https://i.imgur.com/XQ8N2vH.png',
                ),
                mocker.call(
                    mocker.sentinel.webhook_2,
                    mocker.sentinel.get_passage_return_2,
                    thread=discord.utils.MISSING,
                    avatar_url='https://i.imgur.com/XQ8N2vH.png',
                ),
            ]
        )
        assert (
            mock_daily_bread.next_scheduled  # pyright: ignore
            is mocker.sentinel.next_scheduled_time_1
        )
        assert (
            mock_daily_bread_2.next_scheduled  # pyright: ignore
            is mocker.sentinel.next_scheduled_time_2
        )
        mock_db_session.commit.assert_has_awaits(  # pyright: ignore
            [mocker.call(), mocker.call()]
        )

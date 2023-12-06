from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Final

import discord
import pendulum
from attrs import field, frozen
from botus_receptus import re, utils
from bs4 import BeautifulSoup, SoupStrainer
from discord import app_commands
from discord.ext import tasks

from ....data import Passage, VerseRange
from ....db import BibleVersion, DailyBread, Session
from ....exceptions import (
    BookNotInVersionError,
    DailyBreadNotInVersionError,
    DoNotUnderstandError,
    ServiceNotSupportedError,
)
from ....utils import send_passage
from ..bible_lookup import bible_lookup  # noqa: TCH001
from .common import TASK_INTERVAL, get_next_scheduled_time

if TYPE_CHECKING:
    from collections.abc import Callable

    import aiohttp
    from botus_receptus.types import Coroutine

    from ....l10n import GroupLocalizer
    from ....service_manager import ServiceManager
    from ....types import Bible
    from ..types import ParentCog

_log: Final = logging.getLogger(__name__)
_shared_cooldown: Final = app_commands.checks.cooldown(
    rate=2, per=60.0, key=lambda i: (i.guild_id, i.user.id)
)


@frozen
class PassageFetcher:
    verse_range: VerseRange
    service_manager: ServiceManager
    passage_map: dict[int, Passage] = field(init=False, factory=dict)

    def verse_range_in_bible(self, bible: Bible, /) -> bool:
        return self.verse_range.book_mask in bible.books

    async def __call__(self, bible: Bible, /) -> Passage:
        if bible.id in self.passage_map:
            return self.passage_map[bible.id]

        passage = await self.service_manager.get_passage(bible, self.verse_range)
        self.passage_map[bible.id] = passage

        return passage


@app_commands.guild_only()
class DailyBreadGroup(
    app_commands.Group, name='daily-bread', description='Daily bread'
):
    session: aiohttp.ClientSession
    service_manager: ServiceManager
    localizer: GroupLocalizer

    _fetcher: PassageFetcher | None

    def initialize_from_parent(self, parent: ParentCog, /) -> None:
        self.session = parent.bot.session
        self.service_manager = parent.service_manager
        self.localizer = parent.localizer.for_group(self)

        self._fetcher = None

    async def _get_verse_range(self) -> VerseRange:
        async with asyncio.timeout(10), self.session.get(
            'https://www.biblegateway.com/reading-plans/verse-of-the-day'
            '/next?interface=print'
        ) as response:
            text = await response.text(errors='replace')
            strainer = SoupStrainer(
                class_=re.compile(
                    re.WORD_BOUNDARY,
                    'rp-passage-display',
                    re.WORD_BOUNDARY,
                )
            )
            soup = BeautifulSoup(text, 'html.parser', parse_only=strainer)
            passage_node = soup.select_one('.rp-passage-display')

            if passage_node is None:
                raise DoNotUnderstandError

            return VerseRange.from_string(passage_node.get_text(''))

    def _get_fetcher(self, verse_range: VerseRange, /) -> PassageFetcher:
        if self._fetcher is None or self._fetcher.verse_range != verse_range:
            self._fetcher = PassageFetcher(verse_range, self.service_manager)

        return self._fetcher

    async def _fetch_and_post(
        self,
        passage_fetcher: PassageFetcher,
        next_scheduled: pendulum.DateTime,
        daily_bread: DailyBread,
        bible: BibleVersion,
        webhook: discord.Webhook,
        /,
    ) -> None:
        try:
            passage = await passage_fetcher(
                bible  # pyright: ignore[reportGeneralTypeIssues]
            )

            if daily_bread.thread_id is None:
                thread = discord.utils.MISSING
            else:
                thread = discord.Object(daily_bread.thread_id)

            await send_passage(
                webhook,
                passage,
                thread=thread,
                avatar_url='https://i.imgur.com/XQ8N2vH.png',
            )
        except (
            DoNotUnderstandError,
            BookNotInVersionError,
            ServiceNotSupportedError,
        ) as error:
            _log.exception(
                'An error occurred fetching %s from %r for guild %r. '
                'Postponing until tomorrow.',
                passage_fetcher.verse_range,
                bible.name,
                daily_bread.guild_id,
                exc_info=error,
                stack_info=True,
            )
        except discord.NotFound as error:
            if error.code == 10015:
                _log.error(
                    'Webhook missing for guild ID %s. Postponing until tomorrow.',
                    daily_bread.guild_id,
                )

            else:
                _log.exception(
                    'An error occurred while posting the daily bread to guild ID %s',
                    daily_bread.guild_id,
                    exc_info=error,
                    stack_info=True,
                )
                return

        except Exception as error:  # noqa: BLE001
            _log.exception(
                'An error occurred while posting the daily bread to guild ID %s',
                daily_bread.guild_id,
                exc_info=error,
                stack_info=True,
            )

            return

        daily_bread.next_scheduled = next_scheduled

    async def _check_and_post(self) -> None:
        async with Session.begin() as session:
            result = await DailyBread.scheduled(session)

            if not result:
                return

            try:
                verse_range = await self._get_verse_range()
            except asyncio.TimeoutError:
                _log.error(
                    'There was an error getting the daily verse range from '
                    'BibleGateway: The request timed out.'
                )
                return
            except DoNotUnderstandError:
                _log.error(
                    'There was an error getting the daily verse range from '
                    'BibleGateway: The expected HTML elements were not found.'
                )
                return

            passage_fetcher = self._get_fetcher(verse_range)
            fallback = await BibleVersion.get_by_command(session, 'esv')

            for daily_bread in result:
                next_scheduled = get_next_scheduled_time(
                    daily_bread.next_scheduled,
                    daily_bread.time,
                    daily_bread.timezone,
                )

                webhook = discord.Webhook.from_url(
                    f'https://discord.com/api/webhooks/{daily_bread.url}',
                    session=self.session,
                )

                if (
                    daily_bread.prefs is not None
                    and daily_bread.prefs.bible_version is not None
                ):
                    bible = daily_bread.prefs.bible_version
                else:
                    bible = fallback

                if not passage_fetcher.verse_range_in_bible(
                    bible  # pyright: ignore[reportGeneralTypeIssues]
                ):
                    daily_bread.next_scheduled = next_scheduled
                    continue

                await self._fetch_and_post(
                    passage_fetcher,
                    next_scheduled,
                    daily_bread,
                    bible,
                    webhook,
                )

            await session.commit()

    def get_task(self) -> tasks.Loop[Callable[[], Coroutine[None]]]:
        return tasks.loop(
            time=[
                pendulum.time(hour, minute)
                for hour in range(12)
                for minute in range(0, 60, TASK_INTERVAL)
            ],
        )(self._check_and_post)

    @app_commands.command()
    @_shared_cooldown
    @app_commands.describe(
        version='The version to display the daily bread in',
        only_me='Whether to display the daily bread to yourself or everyone',
    )
    async def show(
        self,
        itx: discord.Interaction,
        /,
        version: app_commands.Transform[str | None, bible_lookup] = None,
        only_me: bool = False,
    ) -> None:
        """Display today's daily bread"""

        bible: BibleVersion | None = None

        async with Session() as session:
            if version is not None:
                bible = await BibleVersion.get_by_abbr(session, version)

            if bible is None:
                bible = await BibleVersion.get_for(
                    session, user=itx.user, guild=itx.guild
                )

        passage_fetcher = self._get_fetcher(await self._get_verse_range())

        if not passage_fetcher.verse_range_in_bible(
            bible  # pyright: ignore[reportGeneralTypeIssues]
        ):
            raise DailyBreadNotInVersionError(bible.name)

        passage = await passage_fetcher(
            bible  # pyright: ignore[reportGeneralTypeIssues]
        )

        await send_passage(itx, passage, ephemeral=only_me)

    @app_commands.command()
    @_shared_cooldown
    async def status(self, itx: discord.Interaction, /) -> None:
        """Display the status of automated daily bread posts for this server"""

        if TYPE_CHECKING:
            assert itx.guild is not None

        localizer = self.localizer.for_message('status', locale=itx.locale)

        async with Session.begin() as session:
            daily_bread = await DailyBread.for_guild(session, itx.guild)

            if daily_bread:
                channel = await itx.guild.fetch_channel(
                    daily_bread.thread_id or daily_bread.channel_id
                )
                await utils.send_embed(
                    itx,
                    title=localizer.format('title'),
                    fields=[
                        {
                            'name': localizer.format('channel'),
                            'value': channel.mention,
                            'inline': False,
                        },
                        {
                            'name': localizer.format('next_scheduled'),
                            'value': discord.utils.format_dt(
                                daily_bread.next_scheduled
                            ),
                            'inline': False,
                        },
                    ],
                )
            else:
                await utils.send_embed(itx, description=localizer.format('not_set'))

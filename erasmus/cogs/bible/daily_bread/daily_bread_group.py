from __future__ import annotations

import logging
from itertools import chain
from typing import TYPE_CHECKING, Final

import aiohttp
import async_timeout
import discord
import pendulum
from attrs import define, field
from botus_receptus import re, utils
from bs4 import BeautifulSoup, SoupStrainer
from discord import app_commands
from discord.ext import tasks

from ....data import Passage, VerseRange
from ....db import DailyBread, Session
from ....db.bible import BibleVersion
from ....exceptions import (
    DailyBreadNotInVersionError,
    DoNotUnderstandError,
    ErasmusError,
)
from ....utils import send_passage
from ..bible_lookup import bible_lookup  # noqa: TC002
from .common import TASK_INTERVAL

if TYPE_CHECKING:
    from collections.abc import Callable

    from botus_receptus.types import Coroutine

    from ....l10n import GroupLocalizer
    from ....service_manager import ServiceManager
    from ....types import Bible
    from ..types import ParentCog

_log: Final = logging.getLogger(__name__)
_shared_cooldown: Final = app_commands.checks.cooldown(
    rate=2, per=60.0, key=lambda i: (i.guild_id, i.user.id)
)


@define(frozen=True)
class PassageFetcher:
    verse_range: VerseRange
    service_manager: ServiceManager
    passage_map: dict[int, Passage] = field(init=False, factory=dict)

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

    __fetcher: PassageFetcher | None

    def initialize_from_parent(self, parent: ParentCog, /) -> None:
        self.session = parent.bot.session
        self.service_manager = parent.service_manager
        self.localizer = parent.localizer.for_group(self)

        self.__fetcher = None

    async def __get_verse_range(self) -> VerseRange:
        async with async_timeout.timeout(10), self.session.get(
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

    async def __check_and_post(self) -> None:
        async with Session.begin() as session:
            result = await DailyBread.scheduled(session)

            if not result:
                return

            verse_range = await self.__get_verse_range()

            if self.__fetcher is None or self.__fetcher.verse_range != verse_range:
                self.__fetcher = PassageFetcher(verse_range, self.service_manager)

            fallback = await BibleVersion.get_by_command(session, 'esv')

            for daily_bread in result:
                now = pendulum.now(daily_bread.timezone)
                next_scheduled = daily_bread.next_scheduled.set(
                    year=now.year, month=now.month, day=now.day
                ).add(days=1)

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

                if verse_range.book_mask not in bible.books:
                    daily_bread.next_scheduled = next_scheduled
                    continue

                passage = await self.__fetcher(bible)

                try:
                    await send_passage(
                        webhook,
                        passage,
                        thread=discord.Object(daily_bread.thread_id)
                        if daily_bread.thread_id is not None
                        else discord.utils.MISSING,
                        avatar_url='https://i.imgur.com/XQ8N2vH.png',
                    )
                    daily_bread.next_scheduled = next_scheduled
                except (discord.DiscordException, ErasmusError) as error:
                    _log.exception(
                        'An error occurred while posting the daily bread to '
                        'guild ID %s',
                        daily_bread.guild_id,
                        exc_info=error,
                        stack_info=True,
                    )

            await session.commit()

    def get_task(self) -> tasks.Loop[Callable[[], Coroutine[None]]]:
        return tasks.loop(
            time=[
                pendulum.time(*args)
                for args in chain.from_iterable(
                    [(hour, minute) for minute in range(0, 60, TASK_INTERVAL)]
                    for hour in range(24)
                )
            ],
        )(self.__check_and_post)

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
        '''Display today's daily bread'''

        bible: BibleVersion | None = None

        async with Session() as session:
            if version is not None:
                bible = await BibleVersion.get_by_abbr(session, version)

            if bible is None:
                bible = await BibleVersion.get_for(
                    session, user=itx.user, guild=itx.guild
                )

        if self.__fetcher is None:
            self.__fetcher = PassageFetcher(
                await self.__get_verse_range(), self.service_manager
            )

        if self.__fetcher.verse_range.book_mask not in bible.books:
            raise DailyBreadNotInVersionError(bible.name)

        passage = await self.__fetcher(bible)

        await send_passage(itx, passage, ephemeral=only_me)

    @app_commands.command()
    @_shared_cooldown
    async def status(self, itx: discord.Interaction, /) -> None:
        '''Display the status of automated daily bread posts for this server'''

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

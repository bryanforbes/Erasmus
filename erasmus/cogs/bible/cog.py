from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Callable, Final, cast

import discord
from attrs import define, field
from botus_receptus import Cog, formatting, utils
from discord import app_commands
from discord.ext import commands, tasks

from ...data import Passage, SearchResults, VerseRange
from ...db import BibleVersion, Session
from ...exceptions import (
    BibleNotSupportedError,
    BookMappingInvalid,
    BookNotInVersionError,
    BookNotUnderstoodError,
    DailyBreadNotInVersionError,
    DoNotUnderstandError,
    InvalidTimeError,
    InvalidTimeZoneError,
    InvalidVersionError,
    NoUserVersionError,
    ReferenceNotUnderstoodError,
    ServiceLookupTimeout,
    ServiceNotSupportedError,
    ServiceSearchTimeout,
)
from ...service_manager import ServiceManager
from ...ui_pages import UIPages
from ...utils import send_passage
from .admin_group import BibleAdminGroup
from .bible_lookup import _BibleOption, bible_lookup
from .daily_bread import DailyBreadGroup
from .search_page_source import SearchPageSource
from .server_preferences_group import ServerPreferencesGroup
from .version_group import VersionGroup

if TYPE_CHECKING:
    from botus_receptus.types import Coroutine
    from sqlalchemy.ext.asyncio import AsyncSession

    from ...erasmus import Erasmus
    from ...l10n import Localizer
    from ...types import Bible as _BibleType

_log: Final = logging.getLogger(__name__)

_shared_cooldown = app_commands.checks.cooldown(
    rate=8, per=60.0, key=lambda i: (i.guild_id, i.user.id)
)


@define(frozen=True)
class PassageFetcher:
    verse_range: VerseRange
    service_manager: ServiceManager
    passage_map: dict[int, Passage] = field(init=False, factory=dict)

    async def __call__(self, bible: _BibleType, /) -> Passage:
        if bible.id in self.passage_map:
            return self.passage_map[bible.id]

        passage = await self.service_manager.get_passage(bible, self.verse_range)
        self.passage_map[bible.id] = passage

        return passage


class Bible(Cog['Erasmus']):
    service_manager: ServiceManager
    localizer: Localizer

    admin = BibleAdminGroup()
    version = VersionGroup()
    server_preferences = ServerPreferencesGroup()
    daily_bread = DailyBreadGroup()

    __lookup_cooldown: commands.CooldownMapping[discord.Message]
    __daily_bread_task: tasks.Loop[Callable[[], Coroutine[None]]]

    def __init__(self, bot: Erasmus, /) -> None:
        self.service_manager = ServiceManager.from_config(bot.config, bot.session)
        self.localizer = bot.localizer
        self.__lookup_cooldown = commands.CooldownMapping.from_cooldown(
            rate=8, per=60.0, type=commands.BucketType.user
        )

        super().__init__(bot)

        self.admin.initialize_from_parent(self)
        self.version.initialize_from_parent(self)
        self.server_preferences.initialize_from_parent(self)
        self.daily_bread.initialize_from_parent(self)

    async def refresh(self, session: AsyncSession, /) -> None:
        bible_lookup.clear()
        bible_lookup.update(
            [
                _BibleOption.create(version)
                async for version in BibleVersion.get_all(session, ordered=True)
            ]
        )

    async def cog_load(self) -> None:
        self.__daily_bread_task = self.daily_bread.get_task()
        self.__daily_bread_task.start()
        await self.__daily_bread_task()

        async with Session() as session:
            await self.refresh(session)

    async def cog_unload(self) -> None:
        bible_lookup.clear()

        self.__daily_bread_task.cancel()

    def __get_cooldown_bucket(self, message: discord.Message, /) -> commands.Cooldown:
        bucket = self.__lookup_cooldown.get_bucket(message)

        assert bucket is not None

        retry_after = bucket.update_rate_limit(message.created_at.timestamp())

        if retry_after is not None:
            raise app_commands.CommandOnCooldown(bucket, retry_after)

        return bucket

    async def __lookup(
        self,
        itx: discord.Interaction | discord.Message,
        /,
        bible: BibleVersion,
        reference: VerseRange,
        only_me: bool = False,
    ) -> None:
        if reference.book_mask not in bible.books:
            raise BookNotInVersionError(reference.book.name, bible.name)

        passage = await self.service_manager.get_passage(bible, reference)
        await send_passage(itx, passage, ephemeral=only_me)

    async def cog_app_command_error(  # pyright: ignore [reportIncompatibleMethodOverride]  # noqa: B950
        self,
        itx: discord.Interaction | discord.Message,
        error: Exception,
    ) -> None:
        if (
            isinstance(
                error,
                (
                    app_commands.CommandInvokeError,
                    app_commands.TransformerError,
                ),
            )
            and error.__cause__ is not None
        ):
            error = cast('Exception', error.__cause__)

        data: dict[str, object] | None = None

        match error:
            case BookNotUnderstoodError():
                message_id = 'book-not-understood'
                data = {'book': error.book}
            case BookNotInVersionError():
                message_id = 'book-not-in-version'
                data = {'book': error.book, 'version': error.version}
            case BookMappingInvalid():
                message_id = 'book-mapping-invalid'
                data = {
                    'book': error.from_book.name,
                    'version': error.version,
                }

                _log.exception(
                    'The mapping "%s" -> "%s" is invalid for "%s"',
                    error.from_book.osis,
                    error.to_osis,
                    error.version,
                    exc_info=error,
                    stack_info=True,
                )
            case DoNotUnderstandError():
                message_id = 'do-not-understand'
            case ReferenceNotUnderstoodError():
                message_id = 'reference-not-understood'
                data = {'reference': error.reference}
            case BibleNotSupportedError():
                data = {'version': error.version}
                message_id = 'bible-not-supported'
            case NoUserVersionError():
                message_id = 'no-user-version'
            case InvalidVersionError():
                message_id = 'invalid-version'
                data = {'version': error.version}
            case ServiceNotSupportedError():
                version_text = f'{error.bible.name}'
                message_id = 'service-not-supported'
                data = {'name': version_text}
            case ServiceLookupTimeout():
                message_id = 'service-lookup-timeout'
                data = {'name': error.bible.name, 'verses': str(error.verses)}
            case ServiceSearchTimeout():
                message_id = 'service-search-timeout'
                data = {'name': error.bible.name, 'terms': ' '.join(error.terms)}
            case InvalidTimeError():
                message_id = 'invalid-time'
                data = {'time': error.time}
            case InvalidTimeZoneError():
                message_id = 'invalid-timezone'
                data = {'timezone': error.timezone}
            case DailyBreadNotInVersionError():
                message_id = 'daily-bread-not-in-version'
                data = {'version': error.version}
            case _:
                return

        await utils.send_embed_error(
            itx,
            description=formatting.escape(
                self.localizer.format(
                    message_id,
                    data=data,
                    locale=itx.locale if isinstance(itx, discord.Interaction) else None,
                ),
                mass_mentions=True,
            ),
        )

    async def lookup_from_message(self, message: discord.Message, /) -> None:
        try:
            verse_ranges = VerseRange.get_all_from_string(
                message.content,
                only_bracketed=self.bot.user not in message.mentions,  # pyright: ignore
            )

            if not verse_ranges:
                return

            bucket = self.__get_cooldown_bucket(message)

            async with message.channel.typing(), Session() as session:
                user_bible = await BibleVersion.get_for(
                    session, user=message.author, guild=message.guild
                )

                for i, verse_range in enumerate(verse_ranges):
                    if i > 0:
                        bucket.update_rate_limit()

                    bible: BibleVersion | None = None

                    if isinstance(verse_range, Exception):
                        raise verse_range

                    if verse_range.version is not None:
                        bible = await BibleVersion.get_by_abbr(
                            session, verse_range.version
                        )

                    if bible is None:
                        bible = user_bible

                    await self.__lookup(message, bible, verse_range)
        except Exception as exc:  # noqa: PIE786
            await self.cog_app_command_error(message, exc)
            await self.bot.on_app_command_error(message, exc)

    @app_commands.command()
    @_shared_cooldown
    @app_commands.describe(
        reference='A verse reference',
        version='The version in which to look up the verse',
        only_me='Whether to display the verse to yourself or everyone',
    )
    async def verse(
        self,
        itx: discord.Interaction,
        /,
        reference: VerseRange,
        version: app_commands.Transform[str | None, bible_lookup] = None,
        only_me: bool = False,
    ) -> None:
        '''Look up a verse'''

        bible: BibleVersion | None = None

        if version is not None:
            reference = reference.with_version(version)

        async with Session() as session:
            if reference.version is not None:
                bible = await BibleVersion.get_by_abbr(session, reference.version)

            if bible is None:
                bible = await BibleVersion.get_for(
                    session, user=itx.user, guild=itx.guild
                )

        await itx.response.defer(thinking=True, ephemeral=only_me)
        await self.__lookup(itx, bible, reference, only_me=only_me)

    @app_commands.command()
    @_shared_cooldown
    @app_commands.describe(
        terms='Terms to search for', version='The Bible version to search within'
    )
    async def search(
        self,
        itx: discord.Interaction,
        /,
        terms: str,
        version: app_commands.Transform[str | None, bible_lookup] = None,
    ) -> None:
        '''Search in the Bible'''

        bible: BibleVersion | None = None

        async with Session() as session:
            if version is not None:
                bible = await BibleVersion.get_by_abbr(session, version)

            if bible is None:
                bible = await BibleVersion.get_for(
                    session, user=itx.user, guild=itx.guild
                )

        def search(*, per_page: int, page_number: int) -> Coroutine[SearchResults]:
            return self.service_manager.search(
                bible, terms.split(' '), limit=per_page, offset=page_number
            )

        localizer = self.localizer.for_message('search', itx.locale)
        source = SearchPageSource(search, per_page=5, bible=bible, localizer=localizer)
        view = UIPages(itx, source, localizer=localizer)
        await view.start()

    @app_commands.command()
    @app_commands.checks.cooldown(
        rate=2, per=30.0, key=lambda i: (i.guild_id, i.user.id)
    )
    async def bibles(self, itx: discord.Interaction, /) -> None:
        '''List which Bible versions are available for lookup and search'''

        async with Session() as session:
            lines = [self.localizer.format('bibles.prefix', locale=itx.locale), ''] + [
                f'  {version.name} (`{version.command}`)'
                async for version in BibleVersion.get_all(session, ordered=True)
            ]

        output = '\n'.join(lines)
        await utils.send_embed(itx, description=output)

    @app_commands.command()
    @_shared_cooldown
    @app_commands.describe(version='The Bible version to get information for')
    async def bibleinfo(
        self,
        itx: discord.Interaction,
        /,
        version: app_commands.Transform[str, bible_lookup],
    ) -> None:
        '''Get information about a Bible version'''

        async with Session() as session:
            existing = await BibleVersion.get_by_command(session, version)

        localizer = self.localizer.for_message('bibleinfo', locale=itx.locale)

        await utils.send_embed(
            itx,
            title=existing.name,
            fields=[
                {
                    'name': localizer.format('abbreviation'),
                    'value': existing.command,
                },
                {
                    'name': localizer.format('books'),
                    'value': '\n'.join(existing.books.book_names),
                    'inline': False,
                },
            ],
        )

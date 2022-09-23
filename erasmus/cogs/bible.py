from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Final, cast

import discord
import orjson
from asyncpg.exceptions import UniqueViolationError
from attrs import define
from botus_receptus import Cog, formatting, utils
from botus_receptus.app_commands import admin_guild_only
from discord import app_commands
from discord.ext import commands
from sqlalchemy.exc import IntegrityError

from ..data import Passage, SearchResults, SectionFlag, VerseRange
from ..db import BibleVersion, GuildPref, Session, UserPref
from ..exceptions import (
    BibleNotSupportedError,
    BookMappingInvalid,
    BookNotInVersionError,
    BookNotUnderstoodError,
    DoNotUnderstandError,
    ErasmusError,
    InvalidVersionError,
    NoUserVersionError,
    ReferenceNotUnderstoodError,
    ServiceLookupTimeout,
    ServiceNotSupportedError,
    ServiceSearchTimeout,
)
from ..page_source import AsyncCallback, AsyncPageSource, FieldPageSource, Pages
from ..service_manager import ServiceManager
from ..ui_pages import UIPages
from ..utils import AutoCompleter, send_passage

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Iterable, Sequence
    from typing_extensions import Self

    from botus_receptus.types import Coroutine
    from sqlalchemy.ext.asyncio import AsyncSession

    from ..erasmus import Erasmus
    from ..l10n import Localizer, MessageLocalizer
    from ..types import Bible as _Bible

_log: Final = logging.getLogger(__name__)


def _decode_book_mapping(book_mapping: str | None) -> dict[str, str] | None:
    return orjson.loads(book_mapping) if book_mapping is not None else None


class SearchPageSource(FieldPageSource['Sequence[Passage]'], AsyncPageSource[Passage]):
    bible: _Bible
    localizer: MessageLocalizer

    def __init__(
        self,
        callback: AsyncCallback[Passage],
        /,
        *,
        per_page: int,
        bible: _Bible,
        localizer: MessageLocalizer,
    ) -> None:
        super().__init__(callback, per_page=per_page)

        self.bible = bible
        self.localizer = localizer

    def get_field_values(
        self, entries: Sequence[Passage], /
    ) -> Iterable[tuple[str, str]]:
        for entry in entries:
            yield str(entry.range), (
                entry.text if len(entry.text) < 1024 else f'{entry.text[:1023]}\u2026'
            )

    def format_footer_text(
        self, pages: Pages[Sequence[Passage]], max_pages: int
    ) -> str:
        return self.localizer.format(
            'footer',
            data={
                'current_page': pages.current_page + 1,
                'max_pages': max_pages,
                'total': self.get_total(),
            },
        )

    async def set_page_text(self, page: Sequence[Passage] | None, /) -> None:
        self.embed.title = self.localizer.format(
            'title', data={'bible_name': self.bible.name}
        )

        if page is None:
            self.embed.description = self.localizer.format('no-results')
            return

        await super().set_page_text(page)


@define(frozen=True)
class _BibleOption:
    name: str
    name_lower: str
    command: str
    command_lower: str
    abbreviation: str
    abbreviation_lower: str

    @property
    def key(self) -> str:
        return self.command

    def matches(self, text: str, /) -> bool:
        return (
            self.command_lower.startswith(text)
            or text in self.name_lower
            or text in self.abbreviation_lower
        )

    def choice(self) -> app_commands.Choice[str]:
        return app_commands.Choice(name=self.name, value=self.command)

    @classmethod
    def create(cls, version: BibleVersion, /) -> Self:
        return cls(
            name=version.name,
            name_lower=version.name.lower(),
            command=version.command,
            command_lower=version.command.lower(),
            abbreviation=version.abbr,
            abbreviation_lower=version.abbr.lower(),
        )


class ServiceAutoCompleter(app_commands.Transformer):
    service_manager: ServiceManager

    async def transform(self, itx: discord.Interaction, value: str, /) -> str:
        return value

    async def autocomplete(  # pyright: ignore [reportIncompatibleMethodOverride]
        self, itx: discord.Interaction, value: str, /
    ) -> list[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=service_name, value=service_name)
            for service_name in self.service_manager.service_map.keys()
            if value.lower() in service_name.lower()
        ][:25]


_bible_lookup: AutoCompleter[_BibleOption] = AutoCompleter()
_service_lookup = ServiceAutoCompleter()


@app_commands.default_permissions(administrator=True)
@app_commands.guild_only()
class ServerPreferencesGroup(
    app_commands.Group, name='serverprefs', description='Server preferences'
):
    localizer: Localizer

    def initialize_from_cog(self, cog: Bible, /) -> None:
        self.localizer = cog.localizer

    @app_commands.command()
    @app_commands.describe(version='Bible version')
    @app_commands.checks.cooldown(
        rate=2, per=60.0, key=lambda i: (i.guild_id, i.user.id)
    )
    async def setdefault(
        self,
        itx: discord.Interaction,
        /,
        version: app_commands.Transform[str, _bible_lookup],
    ) -> None:
        '''Set the default version for this server'''

        assert itx.guild is not None

        version = version.lower()

        async with Session.begin() as session:
            existing = await BibleVersion.get_by_command(session, version)
            await existing.set_for_guild(session, itx.guild)

        await utils.send_embed(
            itx,
            description=self.localizer.format(
                'serverprefs__setdefault.response',
                data={'version': version},
                locale=itx.locale,
            ),
            ephemeral=True,
        )

    @app_commands.command()
    @app_commands.checks.cooldown(
        rate=2, per=60.0, key=lambda i: (i.guild_id, i.user.id)
    )
    async def unsetdefault(self, itx: discord.Interaction, /) -> None:
        '''Unset the default version for this server'''

        assert itx.guild is not None

        async with Session.begin() as session:
            if (guild_prefs := await session.get(GuildPref, itx.guild.id)) is not None:
                await session.delete(guild_prefs)
                attribute_id = 'deleted'
            else:
                attribute_id = 'already-deleted'

        await utils.send_embed(
            itx,
            description=self.localizer.format(
                f'serverprefs__unsetdefault.{attribute_id}', locale=itx.locale
            ),
            ephemeral=True,
        )


class PreferencesGroup(app_commands.Group, name='prefs', description='Preferences'):
    localizer: Localizer

    def initialize_from_cog(self, cog: Bible, /) -> None:
        self.localizer = cog.localizer

    @app_commands.command()
    @app_commands.describe(version='Bible version')
    @app_commands.checks.cooldown(rate=2, per=60.0, key=lambda i: i.user.id)
    async def setdefault(
        self,
        itx: discord.Interaction,
        /,
        version: app_commands.Transform[str, _bible_lookup],
    ) -> None:
        '''Set your default Bible version'''
        version = version.lower()

        async with Session.begin() as session:
            existing = await BibleVersion.get_by_command(session, version)
            await existing.set_for_user(session, itx.user)

        await utils.send_embed(
            itx,
            description=self.localizer.format(
                'prefs__setdefault.response',
                data={'version': version},
                locale=itx.locale,
            ),
            ephemeral=True,
        )

    @app_commands.command()
    @app_commands.checks.cooldown(rate=2, per=60.0, key=lambda i: i.user.id)
    async def unsetdefault(self, itx: discord.Interaction, /) -> None:
        '''Unset your default Bible version'''
        async with Session.begin() as session:
            user_prefs = await session.get(UserPref, itx.user.id)

            if user_prefs is not None:
                await session.delete(user_prefs)
                attribute_id = 'deleted'
            else:
                attribute_id = 'already-deleted'

        await utils.send_embed(
            itx,
            description=self.localizer.format(
                f'prefs__unsetdefault.{attribute_id}', locale=itx.locale
            ),
            ephemeral=True,
        )


@admin_guild_only()
class BibleAdminGroup(app_commands.Group, name='bibleadmin'):
    service_manager: ServiceManager
    refresh_data: Callable[[AsyncSession], Awaitable[None]]

    def initialize_from_cog(self, cog: Bible, /) -> None:
        self.service_manager = cog.service_manager
        self.refresh_data = cog.refresh

    @app_commands.command()
    @app_commands.describe(version='The Bible version to get information for')
    async def info(
        self,
        itx: discord.Interaction,
        /,
        version: app_commands.Transform[str, _bible_lookup],
    ) -> None:
        '''Get information for a Bible version'''

        async with Session() as session:
            existing = await BibleVersion.get_by_command(session, version)

        await utils.send_embed(
            itx,
            title=existing.name,
            fields=[
                {'name': 'Command', 'value': existing.command},
                {'name': 'Abbreviation', 'value': existing.abbr},
                {'name': 'Right to left', 'value': 'Yes' if existing.rtl else 'No'},
                {
                    'name': 'Books',
                    'value': '\n'.join(existing.books.book_names),
                    'inline': False,
                },
                {'name': 'Service', 'value': existing.service},
                {'name': 'Service Version', 'value': existing.service_version},
            ],
        )

    @app_commands.command()
    @app_commands.describe(
        command='The unique command',
        name='The name of the Bible version',
        abbreviation='The abbreviated form of the Bible version',
        service='Service to use for lookup and search',
        service_version="The service's code for this version",
        books='Books included in this version',
        rtl='Whether text is right-to-left or not',
    )
    async def add(
        self,
        itx: discord.Interaction,
        /,
        command: str,
        name: str,
        abbreviation: str,
        service: app_commands.Transform[str, _service_lookup],
        service_version: str,
        books: str = 'OT,NT',
        rtl: bool = False,
        book_mapping: str | None = None,
    ) -> None:
        '''Add a Bible version'''

        if service not in self.service_manager:
            await utils.send_embed_error(
                itx,
                description=f'`{service}` is not a valid service',
            )
            return

        try:
            async with Session.begin() as session:
                bible = BibleVersion.create(
                    command=command,
                    name=name,
                    abbr=abbreviation,
                    service=service,
                    service_version=service_version,
                    books=books,
                    rtl=rtl,
                    book_mapping=_decode_book_mapping(book_mapping),
                )
                session.add(bible)

                await session.commit()

            async with Session() as session:
                await self.refresh_data(session)
        except (UniqueViolationError, IntegrityError):
            await utils.send_embed_error(
                itx,
                description=f'`{command}` already exists',
            )
        except orjson.JSONDecodeError:
            await utils.send_embed_error(
                itx,
                description=f'`{book_mapping}` is invalid JSON',
            )
        else:
            await utils.send_embed(
                itx,
                description=f'Added `{command}` as "{name}"',
                color=discord.Colour.green(),
            )

    @app_commands.command()
    @app_commands.describe(version='The version to delete')
    async def delete(
        self,
        itx: discord.Interaction,
        /,
        version: app_commands.Transform[str, _bible_lookup],
    ) -> None:
        '''Delete a Bible'''

        async with Session.begin() as session:
            existing = await BibleVersion.get_by_command(session, version)
            _bible_lookup.discard(existing.command)
            await session.delete(existing)

        await utils.send_embed(
            itx,
            description=f'Removed `{existing.command}`',
        )

    @app_commands.command()
    @app_commands.describe(
        version='The version to update',
        service='Service to use for lookup and search',
        service_version="The service's code for this version",
    )
    async def update(
        self,
        itx: discord.Interaction,
        /,
        version: app_commands.Transform[str, _bible_lookup],
        name: str | None = None,
        abbreviation: str | None = None,
        service: app_commands.Transform[str | None, _service_lookup] = None,
        service_version: str | None = None,
        rtl: bool | None = None,
        books: str | None = None,
        book_mapping: str | None = None,
    ) -> None:
        '''Update a Bible'''

        if service is not None and service not in self.service_manager:
            await utils.send_embed_error(
                itx,
                description=f'`{service}` is not a valid service',
            )
            return

        try:
            async with Session.begin() as session:
                bible = await BibleVersion.get_by_command(session, version)

                if name is not None:
                    bible.name = name

                if abbreviation is not None:
                    bible.abbr = abbreviation

                if service is not None:
                    bible.service = service

                if service_version is not None:
                    bible.service_version = service_version

                if rtl is not None:
                    bible.rtl = rtl

                if books is not None:
                    bible.books = SectionFlag.from_book_names(books)

                if book_mapping is not None:
                    bible.book_mapping = _decode_book_mapping(book_mapping)

                await session.commit()

            async with Session() as session:
                await self.refresh_data(session)
        except orjson.JSONDecodeError:
            await utils.send_embed_error(
                itx,
                description=f'`{book_mapping}` is invalid JSON',
            )
        except ErasmusError:
            raise
        except Exception:  # noqa: PIE786
            await utils.send_embed_error(itx, description=f'Error updating `{version}`')
        else:
            await utils.send_embed(itx, description=f'Updated `{version}`')


_shared_cooldown = app_commands.checks.cooldown(
    rate=8, per=60.0, key=lambda i: (i.guild_id, i.user.id)
)


class Bible(Cog['Erasmus']):
    service_manager: ServiceManager
    localizer: Localizer

    admin = BibleAdminGroup()
    preferences = PreferencesGroup()
    server_preferences = ServerPreferencesGroup()

    __lookup_cooldown: commands.CooldownMapping[discord.Message]

    def __init__(self, bot: Erasmus, /) -> None:
        self.service_manager = ServiceManager.from_config(bot.config, bot.session)
        self.localizer = bot.localizer
        self.__lookup_cooldown = commands.CooldownMapping.from_cooldown(
            rate=8, per=60.0, type=commands.BucketType.user
        )

        super().__init__(bot)

        self.admin.initialize_from_cog(self)
        self.preferences.initialize_from_cog(self)
        self.server_preferences.initialize_from_cog(self)

        _service_lookup.service_manager = self.service_manager

    async def refresh(self, session: AsyncSession, /) -> None:
        _bible_lookup.clear()
        _bible_lookup.update(
            [
                _BibleOption.create(version)
                async for version in BibleVersion.get_all(session, ordered=True)
            ]
        )

    async def cog_load(self) -> None:
        async with Session() as session:
            await self.refresh(session)

    async def cog_unload(self) -> None:
        _bible_lookup.clear()

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
        if not bible.books & reference.book_mask:
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
                user_bible = await BibleVersion.get_for_user(
                    session, message.author, message.guild
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
        version: app_commands.Transform[str | None, _bible_lookup] = None,
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
                bible = await BibleVersion.get_for_user(session, itx.user, itx.guild)

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
        version: app_commands.Transform[str | None, _bible_lookup] = None,
    ) -> None:
        '''Search in the Bible'''

        bible: BibleVersion | None = None

        async with Session() as session:
            if version is not None:
                bible = await BibleVersion.get_by_abbr(session, version)

            if bible is None:
                bible = await BibleVersion.get_for_user(session, itx.user, itx.guild)

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
        version: app_commands.Transform[str, _bible_lookup],
    ) -> None:
        '''Get information about a Bible version'''

        async with Session() as session:
            existing = await BibleVersion.get_by_command(session, version)

        await utils.send_embed(
            itx,
            title=existing.name,
            fields=[
                {
                    'name': self.localizer.format(
                        'bibleinfo.abbreviation', locale=itx.locale
                    ),
                    'value': existing.command,
                },
                {
                    'name': self.localizer.format('bibleinfo.books', locale=itx.locale),
                    'value': '\n'.join(existing.books.book_names),
                    'inline': False,
                },
            ],
        )


async def setup(bot: Erasmus, /) -> None:
    await bot.add_cog(Bible(bot))

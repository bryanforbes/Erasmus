from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final, cast

import discord
from asyncpg.exceptions import UniqueViolationError
from attrs import define
from botus_receptus import Cog, checks, formatting, utils
from botus_receptus.app_commands import admin_guild_only
from discord import app_commands
from discord.ext import commands

from ..data import Passage, SearchResults, VerseRange, get_book_data, get_books_for_mask
from ..db import BibleVersion, GuildPref, Session, UserPref
from ..exceptions import (
    BibleNotSupportedError,
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
    from collections.abc import Iterable, Iterator, Sequence
    from typing_extensions import Self

    from botus_receptus.types import Coroutine

    from ..erasmus import Erasmus
    from ..l10n import Localizer, MessageLocalizer
    from ..types import Bible as _Bible


def _book_mask_from_books(books: str, /) -> int:
    book_mask = 0

    for book in books.split(','):
        book = book.strip()
        if book == 'OT':
            book = 'Genesis'
        elif book == 'NT':
            book = 'Matthew'

        book_data = get_book_data(book)

        if book_data['section'] == 'DC':
            continue

        book_mask = book_mask | book_data['section']

    return book_mask


def _book_names_from_book_mask(book_mask: int, /) -> Iterator[str]:
    for book in get_books_for_mask(book_mask):
        match book['name']:
            case 'Genesis':
                yield 'Old Testament'
            case 'Matthew':
                yield 'New Testament'
            case _:
                yield book['name']


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
        self,
        entries: Sequence[Passage],
        /,
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


_lookup_help: Final = '''
Arguments:
----------
    <reference> - A verse reference in one of the following forms:
        Book 1:1
        Book 1:1-2
        Book 1:1-2:1

Example:
--------
    {prefix} John 1:50-2:1

NOTE: Before this command will work, you MUST set your prefered Bible version
      using {prefix}setversion'''

_search_help: Final = '''
Arguments:
----------
    [terms...] - One or more terms to search for

Example:
--------
    {prefix}s faith hope

NOTE: Before this command will work, you MUST set your prefered Bible version
      using {prefix}setversion'''

_setversion_help: Final = '''
Arguments:
----------
    <version> - A supported version identifier listed in {prefix}versions

Example:
--------
    {prefix}setversion nasb'''

_unsetversion_help: Final = '''

Example:
--------
    {prefix}unsetversion'''

_setguildversion_help: Final = '''
Arguments:
----------
    <version> - A supported version identifier listed in {prefix}versions

Example:
--------
    {prefix}setguildversion nasb'''

_unsetguildversion_help: Final = '''

Example:
--------
    {prefix}unsetguildversion'''

_version_lookup_help: Final = '''
Arguments:
----------
    <reference> - A verse reference in one of the following forms:
        Book 1:1
        Book 1:1-2
        Book 1:1-2:1

Example:
--------
    {prefix}{command} John 1:50-2:1'''


_version_search_help: Final = '''
Arguments:
----------
    [terms...] - One or more terms to search for

Example:
--------
    {prefix}{command} faith hope'''


class BibleBase(Cog['Erasmus']):
    service_manager: ServiceManager
    localizer: Localizer

    def __init__(
        self,
        bot: Erasmus,
        service_manager: ServiceManager,
        /,
    ) -> None:
        self.service_manager = service_manager
        self.localizer = bot.localizer

        super().__init__(bot)

    async def cog_command_error(
        self,
        ctx: commands.Context[Any] | discord.Interaction,
        error: Exception,
    ) -> None:
        if (
            isinstance(
                error,
                (
                    commands.CommandInvokeError,
                    commands.BadArgument,
                    commands.ConversionError,
                    app_commands.CommandInvokeError,
                    app_commands.TransformerError,
                ),
            )
            and error.__cause__ is not None
        ):
            error = cast('Exception', error.__cause__)

        data: dict[str, Any] | None = None

        match error:
            case BookNotUnderstoodError():
                message_id = 'book-not-understood'
                data = {'book': error.book}
            case BookNotInVersionError():
                message_id = 'book-not-in-version'
                data = {'book': error.book, 'version': error.version}
            case DoNotUnderstandError():
                message_id = 'do-not-understand'
            case ReferenceNotUnderstoodError():
                message_id = 'reference-not-understood'
                data = {'reference': error.reference}
            case BibleNotSupportedError():
                if isinstance(ctx, commands.Context):
                    data = {'version': f'{ctx.prefix}{error.version}'}
                else:
                    data = {'version': error.version}
                message_id = 'bible-not-supported'
            case NoUserVersionError():
                message_id = 'no-user-version'
            case InvalidVersionError():
                message_id = 'invalid-version'
                data = {'version': error.version}
            case ServiceNotSupportedError():
                if isinstance(ctx, commands.Context):
                    version_text = f'{ctx.prefix}{ctx.invoked_with}'
                else:
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
            ctx,
            description=formatting.escape(
                self.localizer.format(
                    message_id,
                    data=data,
                    locale=ctx.locale
                    if isinstance(ctx, discord.Interaction)
                    else (
                        ctx.interaction.locale if ctx.interaction is not None else None
                    ),
                ),
                mass_mentions=True,
            ),
        )

    cog_app_command_error = cog_command_error  # type: ignore


class Bible(BibleBase):
    async def cog_load(self) -> None:
        self._user_cooldown = commands.CooldownMapping.from_cooldown(
            8, 60.0, commands.BucketType.user
        )

        # Share cooldown across commands
        self.lookup._buckets = self.search._buckets = self._user_cooldown

        async with Session() as session:
            async for version in BibleVersion.get_all(session):
                self.__add_bible_commands(version.command, version.name)

    async def cog_unload(self) -> None:
        async with Session() as session:
            async for version in BibleVersion.get_all(session):
                self.__remove_bible_commands(version.command)

    async def lookup_from_message(
        self,
        ctx: commands.Context[Erasmus],
        message: discord.Message,
        /,
    ) -> None:
        try:
            verse_ranges = VerseRange.get_all_from_string(
                message.content,
                only_bracketed=self.bot.user not in message.mentions,  # type: ignore
            )

            if len(verse_ranges) == 0:
                return

            bucket = self._user_cooldown.get_bucket(ctx.message)
            assert bucket is not None

            retry_after = bucket.update_rate_limit()

            if retry_after:
                raise commands.CommandOnCooldown(
                    bucket, retry_after, commands.BucketType.user
                )

            await self.bot._application_command_notice(ctx)

            async with ctx.typing():
                async with Session() as session:
                    user_bible = await BibleVersion.get_for_user(
                        session, ctx.author, ctx.guild
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

                        await self.__lookup(ctx, bible, verse_range)
        except Exception as exc:  # noqa: PIE786
            await self.cog_command_error(ctx, exc)
            await self.bot.on_command_error(ctx, exc)

    @commands.command(
        aliases=[''],
        brief='Look up a verse in your preferred version',
        help=_lookup_help,
    )
    async def lookup(
        self, ctx: commands.Context[Erasmus], /, *, reference: VerseRange
    ) -> None:
        async with Session() as session:
            bible = await BibleVersion.get_for_user(session, ctx.author, ctx.guild)

        async with ctx.typing():
            await self.__lookup(ctx, bible, reference)

    @commands.command(
        aliases=['s'],
        brief='Search for terms in your preferred version',
        help=_search_help,
    )
    async def search(self, ctx: commands.Context[Erasmus], /, *terms: str) -> None:
        async with Session() as session:
            bible = await BibleVersion.get_for_user(session, ctx.author, ctx.guild)

        await self.__search(ctx, bible, *terms)

    @commands.command(
        brief='List which Bible versions are available for lookup and search'
    )
    @commands.cooldown(rate=2, per=30.0, type=commands.BucketType.channel)
    async def versions(self, ctx: commands.Context[Erasmus], /) -> None:
        lines = ['I support the following Bible versions:', '']

        async with Session() as session:
            lines += [
                f'  `{ctx.prefix}{version.command}`: {version.name}'
                async for version in BibleVersion.get_all(session, ordered=True)
            ]

        lines.append(
            "\nYou can search any version by prefixing the version command with 's' "
            f'(ex. `{ctx.prefix}sesv terms...`)'
        )

        output = '\n'.join(lines)
        await utils.send_embed(ctx, description=f'\n{output}\n')

    @commands.command(brief='Set your preferred version', help=_setversion_help)
    @commands.cooldown(rate=2, per=60.0, type=commands.BucketType.user)
    async def setversion(self, ctx: commands.Context[Erasmus], version: str, /) -> None:
        version = version.lower()
        if version[0] == ctx.prefix:
            version = version[1:]

        async with Session.begin() as session:
            existing = await BibleVersion.get_by_command(session, version)
            await existing.set_for_user(session, ctx.author)

        await utils.send_embed(ctx, description=f'Version set to `{version}`')

    @commands.command(brief='Delete your preferred version', help=_unsetversion_help)
    @commands.cooldown(rate=2, per=60.0, type=commands.BucketType.user)
    async def unsetversion(self, ctx: commands.Context[Erasmus], /) -> None:
        async with Session.begin() as session:
            user_prefs = await session.get(UserPref, ctx.author.id)

            if user_prefs is not None:
                await session.delete(user_prefs)
                await utils.send_embed(ctx, description='Preferred version deleted')
            else:
                await utils.send_embed(
                    ctx, description='Preferred version already deleted'
                )

    @commands.command(brief='Set the guild default version', help=_setguildversion_help)
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.cooldown(rate=2, per=60.0, type=commands.BucketType.user)
    async def setguildversion(
        self,
        ctx: commands.Context[Erasmus],
        version: str,
        /,
    ) -> None:
        assert ctx.guild is not None

        version = version.lower()
        if version[0] == ctx.prefix:
            version = version[1:]

        async with Session.begin() as session:
            existing = await BibleVersion.get_by_command(session, version)
            await existing.set_for_guild(session, ctx.guild)

        await utils.send_embed(ctx, description=f'Guild version set to `{version}`')

    @commands.command(
        brief='Delete the guild default version', help=_unsetguildversion_help
    )
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.cooldown(rate=2, per=60.0, type=commands.BucketType.user)
    async def unsetguildversion(self, ctx: commands.Context[Erasmus], /) -> None:
        assert ctx.guild is not None

        async with Session.begin() as session:
            if (guild_prefs := await session.get(GuildPref, ctx.guild.id)) is not None:
                await session.delete(guild_prefs)
                await utils.send_embed(ctx, description='Guild version deleted')
            else:
                await utils.send_embed(ctx, description='Guild version already deleted')

    @commands.command(name='addbible')
    @checks.dm_only()
    @commands.is_owner()
    async def add_bible(
        self,
        ctx: commands.Context[Erasmus],
        command: str,
        name: str,
        abbr: str,
        service: str,
        service_version: str,
        books: str = 'OT,NT',
        rtl: bool = False,
        /,
    ) -> None:
        if service not in self.service_manager:
            await utils.send_embed_error(
                ctx, description=f'`{service}` is not a valid service'
            )
            return

        try:
            async with Session.begin() as session:
                session.add(
                    BibleVersion(
                        command=command,  # type: ignore
                        name=name,  # type: ignore
                        abbr=abbr,  # type: ignore
                        service=service,  # type: ignore
                        service_version=service_version,  # type: ignore
                        rtl=rtl,  # type: ignore
                        books=_book_mask_from_books(books),  # type: ignore
                    )
                )
        except UniqueViolationError:
            await utils.send_embed_error(ctx, description=f'`{command}` already exists')
        else:
            self.__add_bible_commands(command, name)
            await utils.send_embed(ctx, description=f'Added `{command}` as "{name}"')

    @commands.command(name='delbible')
    @checks.dm_only()
    @commands.is_owner()
    async def delete_bible(
        self,
        ctx: commands.Context[Erasmus],
        command: str,
        /,
    ) -> None:
        async with Session.begin() as session:
            version = await BibleVersion.get_by_command(session, command)
            await session.delete(version)

            self.__remove_bible_commands(command)

            await utils.send_embed(ctx, description=f'Removed `{command}`')

    @commands.command(name='upbible')
    @checks.dm_only()
    @commands.is_owner()
    async def update_bible(
        self,
        ctx: commands.Context[Erasmus],
        command: str,
        service: str,
        service_version: str,
        /,
    ) -> None:
        try:
            async with Session.begin() as session:
                version = await BibleVersion.get_by_command(session, command)
                version.service = service
                version.service_version = service_version
        except ErasmusError:
            raise
        except Exception:  # noqa: PIE786
            await utils.send_embed_error(ctx, description=f'Error updating `{command}`')
        else:
            await utils.send_embed(ctx, description=f'Updated `{command}`')

    async def __version_lookup(
        self, ctx: commands.Context[Erasmus], /, *, reference: VerseRange
    ) -> None:
        async with Session() as session:
            bible = await BibleVersion.get_by_command(
                session, cast('str', ctx.invoked_with)
            )

        async with ctx.typing():
            await self.__lookup(ctx, bible, reference)

    async def __version_search(
        self, ctx: commands.Context[Erasmus], /, *terms: str
    ) -> None:
        async with Session() as session:
            bible = await BibleVersion.get_by_command(
                session, cast('str', ctx.invoked_with)[1:]
            )

        await self.__search(ctx, bible, *terms)

    async def __lookup(
        self,
        ctx: commands.Context[Erasmus],
        bible: BibleVersion,
        reference: VerseRange,
        /,
    ) -> None:
        if reference.book_mask == 'DC' or not (bible.books & reference.book_mask):
            raise BookNotInVersionError(reference.book, bible.name)

        if reference is not None:
            passage = await self.service_manager.get_passage(bible, reference)
            await send_passage(ctx, passage)
        else:
            await utils.send_embed_error(
                ctx, description=f'I do not understand the request `${reference}`'
            )

    async def __search(
        self, ctx: commands.Context[Erasmus], bible: BibleVersion, /, *terms: str
    ) -> None:
        if not terms:
            await utils.send_embed_error(
                ctx, description='Please include some terms to search for'
            )
            return

        def search(*, per_page: int, page_number: int) -> Coroutine[SearchResults]:
            return self.service_manager.search(
                bible, list(terms), limit=per_page, offset=page_number
            )

        localizer = self.localizer.for_message('search')
        source = SearchPageSource(search, per_page=5, bible=bible, localizer=localizer)
        view = UIPages(ctx, source, localizer=localizer)
        await view.start()

    def __add_bible_commands(self, command: str, name: str, /) -> None:
        lookup = commands.Command(
            Bible.__version_lookup,
            name=command,
            brief=f'Look up a verse in {name}',
            help=_version_lookup_help.format(prefix='{prefix}', command=command),
            hidden=True,
            # Share cooldown across commands
            cooldown=self._user_cooldown,
        )
        lookup.cog = self
        search = commands.Command(
            Bible.__version_search,
            name=f's{command}',
            brief=f'Search in {name}',
            help=_version_search_help.format(prefix='{prefix}', command=f's{command}'),
            hidden=True,
            # Share cooldown across commands
            cooldown=self._user_cooldown,
        )
        search.cog = self

        self.bot.add_command(lookup)
        self.bot.add_command(search)

    def __remove_bible_commands(self, command: str, /) -> None:
        self.bot.remove_command(command)
        self.bot.remove_command(f's{command}')


@define
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

    def update(self, version: BibleVersion, /) -> None:
        self.name = version.name
        self.name_lower = version.name.lower()
        self.abbreviation = version.abbr
        self.abbreviation_lower = version.abbr.lower()

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

    async def transform(  # pyright: ignore [reportIncompatibleMethodOverride]
        self,
        itx: discord.Interaction,
        value: str,
        /,
    ) -> str:
        return value

    async def autocomplete(  # pyright: ignore [reportIncompatibleMethodOverride]
        self,
        itx: discord.Interaction,
        value: str,
        /,
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
                    'value': '\n'.join(
                        list(_book_names_from_book_mask(existing.books))
                    ),
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
                bible = BibleVersion(
                    command=command,  # type: ignore
                    name=name,  # type: ignore
                    abbr=abbreviation,  # type: ignore
                    service=service,  # type: ignore
                    service_version=service_version,  # type: ignore
                    rtl=rtl,  # type: ignore
                    books=_book_mask_from_books(books),  # type: ignore
                )
                session.add(bible)
            _bible_lookup.add(_BibleOption.create(bible))
        except UniqueViolationError:
            await utils.send_embed_error(
                itx,
                description=f'`{command}` already exists',
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
    ) -> None:
        '''Update a Bible'''

        if service is not None and service not in self.service_manager:
            await utils.send_embed_error(
                itx,
                description=f'`{service}` is not a valid service',
            ),
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
                    bible.books = _book_mask_from_books(books)

            _bible_lookup.discard(bible.command)
            _bible_lookup.add(_BibleOption.create(bible))

        except ErasmusError:
            raise
        except Exception:  # noqa: PIE786
            await utils.send_embed_error(itx, description=f'Error updating `{version}`')
        else:
            await utils.send_embed(itx, description=f'Updated `{version}`')


_shared_cooldown = app_commands.checks.cooldown(
    rate=8, per=60.0, key=lambda i: (i.guild_id, i.user.id)
)


class BibleAppCommands(BibleBase):
    admin = BibleAdminGroup()
    preferences = PreferencesGroup()
    server_preferences = ServerPreferencesGroup()

    def __init__(
        self,
        bot: Erasmus,
        service_manager: ServiceManager,
        /,
    ) -> None:
        super().__init__(bot, service_manager)

        self.admin.service_manager = service_manager
        self.preferences.localizer = self.localizer
        self.server_preferences.localizer = self.localizer

    async def cog_load(self) -> None:
        async with Session() as session:
            _bible_lookup.clear()
            _bible_lookup.update(
                [
                    _BibleOption.create(version)
                    async for version in BibleVersion.get_all(session, ordered=True)
                ]
            )

    async def cog_unload(self) -> None:
        _bible_lookup.clear()

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
            reference.version = version

        async with Session() as session:
            if reference.version is not None:
                bible = await BibleVersion.get_by_abbr(session, reference.version)

            if bible is None:
                bible = await BibleVersion.get_for_user(session, itx.user, itx.guild)

        if reference.book_mask == 'DC' or not (bible.books & reference.book_mask):
            raise BookNotInVersionError(reference.book, bible.name)

        await itx.response.defer(thinking=True, ephemeral=only_me)
        passage = await self.service_manager.get_passage(bible, reference)
        await send_passage(itx, passage, ephemeral=only_me)

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

        lines = [
            self.localizer.format('bibles.prefix', locale=itx.locale),
            '',
        ]

        async with Session() as session:
            lines += [
                f'  `{version.command}`: {version.name}'
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
                    'value': '\n'.join(
                        list(_book_names_from_book_mask(existing.books))
                    ),
                    'inline': False,
                },
            ],
        )


async def setup(bot: Erasmus, /) -> None:
    service_manager = ServiceManager.from_config(bot.config, bot.session)
    _service_lookup.service_manager = service_manager

    await bot.add_cog(Bible(bot, service_manager))
    await bot.add_cog(BibleAppCommands(bot, service_manager))

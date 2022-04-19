from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
from typing import Any, Final, cast
from typing_extensions import Self

import discord
from attrs import define
from botus_receptus import Cog, checks, formatting, utils
from botus_receptus.app_commands import admin_guild_only
from botus_receptus.db import UniqueViolationError
from discord import app_commands
from discord.ext import commands

from ..data import Passage, SearchResults, VerseRange, get_book_data, get_books_for_mask
from ..db.bible import BibleVersion, GuildPref, UserPref
from ..erasmus import Erasmus
from ..exceptions import (
    BibleNotSupportedError,
    BookNotInVersionError,
    BookNotUnderstoodError,
    DoNotUnderstandError,
    InvalidVersionError,
    NoUserVersionError,
    ReferenceNotUnderstoodError,
    ServiceLookupTimeout,
    ServiceNotSupportedError,
    ServiceSearchTimeout,
)
from ..page_source import AsyncCallback, AsyncPageSource, FieldPageSource
from ..protocols import Bible as _Bible
from ..service_manager import ServiceManager
from ..ui_pages import ContextUIPages, InteractionUIPages
from ..utils import InfoContainer, send_passage


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


class SearchPageSource(FieldPageSource[Sequence[Passage]], AsyncPageSource[Passage]):
    bible: _Bible

    def __init__(
        self, callback: AsyncCallback[Passage], /, *, per_page: int, bible: _Bible
    ) -> None:
        super().__init__(callback, per_page=per_page)

        self.bible = bible

    def get_field_values(
        self,
        entries: Sequence[Passage],
        /,
    ) -> Iterable[tuple[str, str]]:
        for entry in entries:
            yield str(entry.range), entry.text

    async def set_page_text(self, page: Sequence[Passage] | None, /) -> None:
        self.embed.title = f'Search results from {self.bible.name}'

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


class BibleBase(Cog[Erasmus]):
    service_manager: ServiceManager

    def __init__(self, bot: Erasmus, service_manager: ServiceManager, /) -> None:
        self.service_manager = service_manager

        super().__init__(bot)


class Bible(BibleBase):
    async def cog_load(self) -> None:
        self._user_cooldown = commands.CooldownMapping.from_cooldown(
            8, 60.0, commands.BucketType.user
        )

        # Share cooldown across commands
        self.lookup._buckets = self.search._buckets = self._user_cooldown

        async for version in BibleVersion.get_all():
            self.__add_bible_commands(version.command, version.name)

    async def cog_unload(self) -> None:
        async for version in BibleVersion.get_all():
            self.__remove_bible_commands(version.command)

    async def lookup_from_message(
        self,
        ctx: commands.Context[Erasmus],
        message: discord.Message,
        /,
    ) -> None:
        bucket = self._user_cooldown.get_bucket(ctx.message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            raise commands.CommandOnCooldown(
                bucket, retry_after, commands.BucketType.user
            )

        verse_ranges = VerseRange.get_all_from_string(
            message.content,
            only_bracketed=not cast(discord.ClientUser, self.bot.user).mentioned_in(
                message
            ),
        )

        if len(verse_ranges) == 0:
            return

        async with ctx.typing():
            user_bible = await BibleVersion.get_for_user(ctx.author, ctx.guild)

            for i, verse_range in enumerate(verse_ranges):
                if i > 0:
                    bucket.update_rate_limit()

                bible: BibleVersion | None = None

                try:
                    if isinstance(verse_range, Exception):
                        raise verse_range

                    if verse_range.version is not None:
                        bible = await BibleVersion.get_by_abbr(verse_range.version)

                    if bible is None:
                        bible = user_bible

                    await self.__lookup(ctx, bible, verse_range)
                except Exception as exc:
                    await self.bot.on_command_error(ctx, exc)

    async def cog_command_error(self, ctx: commands.Context[Erasmus], error: Exception, /) -> None:  # type: ignore  # noqa: B950
        if (
            isinstance(
                error,
                (
                    commands.CommandInvokeError,
                    commands.BadArgument,
                    commands.ConversionError,
                ),
            )
            and error.__cause__ is not None
        ):
            error = cast(Exception, error.__cause__)

        match error:
            case BookNotUnderstoodError():
                message = f'I do not understand the book "{error.book}"'
            case BookNotInVersionError():
                message = f'{error.version} does not contain {error.book}'
            case DoNotUnderstandError():
                message = 'I do not understand that request'
            case ReferenceNotUnderstoodError():
                message = f'I do not understand the reference "{error.reference}"'
            case BibleNotSupportedError():
                message = f'`{ctx.prefix}{error.version}` is not supported'
            case NoUserVersionError():
                message = (
                    'You must first set your default version with '
                    f'`{ctx.prefix}setversion`'
                )
            case InvalidVersionError():
                message = (
                    f'`{error.version}` is not a valid version. Check '
                    f'`{ctx.prefix}versions` for valid versions'
                )
            case ServiceNotSupportedError():
                message = (
                    f'The service configured for '
                    f'`{self.bot.default_prefix}{ctx.invoked_with}` is not supported'
                )
            case ServiceLookupTimeout():
                message = (
                    f'The request timed out looking up {error.verses} in '
                    + error.bible.name
                )
            case ServiceSearchTimeout():
                message = (
                    f'The request timed out searching for '
                    f'"{" ".join(error.terms)}" in {error.bible.name}'
                )
            case _:
                return

        await utils.send_embed_error(
            ctx, description=formatting.escape(message, mass_mentions=True)
        )

    @commands.command(
        aliases=[''],
        brief='Look up a verse in your preferred version',
        help=_lookup_help,
    )
    async def lookup(
        self, ctx: commands.Context[Erasmus], /, *, reference: VerseRange
    ) -> None:
        bible = await BibleVersion.get_for_user(ctx.author, ctx.guild)

        async with ctx.typing():
            await self.__lookup(ctx, bible, reference)

    @commands.command(
        aliases=['s'],
        brief='Search for terms in your preferred version',
        help=_search_help,
    )
    async def search(self, ctx: commands.Context[Erasmus], /, *terms: str) -> None:
        bible = await BibleVersion.get_for_user(ctx.author, ctx.guild)

        await self.__search(ctx, bible, *terms)

    @commands.command(
        brief='List which Bible versions are available for lookup and search'
    )
    @commands.cooldown(rate=2, per=30.0, type=commands.BucketType.channel)
    async def versions(self, ctx: commands.Context[Erasmus], /) -> None:
        lines = ['I support the following Bible versions:', '']

        lines += [
            f'  `{ctx.prefix}{version.command}`: {version.name}'
            async for version in BibleVersion.get_all(ordered=True)
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

        existing = await BibleVersion.get_by_command(version)
        await existing.set_for_user(ctx.author)

        await utils.send_embed(ctx, description=f'Version set to `{version}`')

    @commands.command(brief='Delete your preferred version', help=_unsetversion_help)
    @commands.cooldown(rate=2, per=60.0, type=commands.BucketType.user)
    async def unsetversion(self, ctx: commands.Context[Erasmus], /) -> None:
        user_prefs = await UserPref.get(ctx.author.id)

        if user_prefs is not None:
            await user_prefs.delete()
            await utils.send_embed(ctx, description='Preferred version deleted')
        else:
            await utils.send_embed(ctx, description='Preferred version already deleted')

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

        existing = await BibleVersion.get_by_command(version)
        await existing.set_for_guild(ctx.guild)

        await utils.send_embed(ctx, description=f'Guild version set to `{version}`')

    @commands.command(
        brief='Delete the guild default version', help=_unsetguildversion_help
    )
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.cooldown(rate=2, per=60.0, type=commands.BucketType.user)
    async def unsetguildversion(self, ctx: commands.Context[Erasmus], /) -> None:
        assert ctx.guild is not None

        if (guild_prefs := await GuildPref.get(ctx.guild.id)) is not None:
            await guild_prefs.delete()
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
            await BibleVersion.create(
                command=command,
                name=name,
                abbr=abbr,
                service=service,
                service_version=service_version,
                rtl=rtl,
                books=_book_mask_from_books(books),
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
        version = await BibleVersion.get_by_command(command)
        await version.delete()

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
        version = await BibleVersion.get_by_command(command)

        try:
            await version.update(
                service=service, service_version=service_version
            ).apply()
        except Exception:
            await utils.send_embed_error(ctx, description=f'Error updating `{command}`')
        else:
            await utils.send_embed(ctx, description=f'Updated `{command}`')

    async def __version_lookup(
        self, ctx: commands.Context[Erasmus], /, *, reference: VerseRange
    ) -> None:
        bible = await BibleVersion.get_by_command(cast(str, ctx.invoked_with))

        async with ctx.typing():
            await self.__lookup(ctx, bible, reference)

    async def __version_search(
        self, ctx: commands.Context[Erasmus], /, *terms: str
    ) -> None:
        bible = await BibleVersion.get_by_command(cast(str, ctx.invoked_with)[1:])

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
            passage = await self.service_manager.get_passage(
                cast(Any, bible), reference
            )
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

        async def search(*, per_page: int, page_number: int) -> SearchResults:
            return await self.service_manager.search(
                bible.as_bible(), list(terms), limit=per_page, offset=page_number
            )

        source = SearchPageSource(search, per_page=5, bible=bible.as_bible())
        view = ContextUIPages(source, ctx=ctx)
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
class _BibleInfo:
    name: str
    name_lower: str
    command: str
    command_lower: str
    abbreviation: str
    abbreviation_lower: str

    @property
    def display_name(self) -> str:
        return self.name

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


_bible_info = InfoContainer(info_cls=_BibleInfo)


async def _version_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    return _bible_info.choices(current)


class PreferencesGroup(
    app_commands.Group, name='prefs', description='Preferences commands'
):
    @app_commands.command()
    @app_commands.describe(version='Bible version')
    @app_commands.checks.cooldown(rate=2, per=60.0, key=lambda i: i.user.id)
    @app_commands.autocomplete(version=_version_autocomplete)
    async def setdefault(
        self,
        interaction: discord.Interaction,
        /,
        version: str,
    ) -> None:
        '''Set your default Bible version'''
        version = version.lower()

        existing = await BibleVersion.get_by_command(version)
        await existing.set_for_user(interaction.user)

        await utils.send_embed(
            interaction,
            description=f'Version set to `{version}`',
            ephemeral=True,
        )

    @app_commands.command()
    @app_commands.checks.cooldown(rate=2, per=60.0, key=lambda i: i.user.id)
    async def unsetdefault(self, interaction: discord.Interaction, /) -> None:
        '''Unset your default Bible version'''
        user_prefs = await UserPref.get(interaction.user.id)

        if user_prefs is not None:
            await user_prefs.delete()
            description = 'Default version unset'
        else:
            description = 'Default version already unset'

        await utils.send_embed(interaction, description=description, ephemeral=True)

    @app_commands.command()
    @app_commands.describe(version='Bible version')
    @app_commands.checks.cooldown(
        rate=2, per=60.0, key=lambda i: (i.guild_id, i.user.id)
    )
    @app_commands.autocomplete(version=_version_autocomplete)
    @app_commands.checks.has_permissions(administrator=True)
    async def setserverdefault(
        self,
        interaction: discord.Interaction,
        /,
        version: str,
    ) -> None:
        '''Set the default version for this server (admin-only)'''

        assert interaction.guild is not None

        version = version.lower()

        existing = await BibleVersion.get_by_command(version)
        await existing.set_for_guild(interaction.guild)

        await utils.send_embed(
            interaction,
            description=f'Server version set to `{version}`',
            ephemeral=True,
        )

    @app_commands.command()
    @app_commands.checks.cooldown(
        rate=2, per=60.0, key=lambda i: (i.guild_id, i.user.id)
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def unsetserverdefault(self, interaction: discord.Interaction, /) -> None:
        '''Unset the default version for this server (admin-only)'''

        assert interaction.guild is not None

        if (guild_prefs := await GuildPref.get(interaction.guild.id)) is not None:
            await guild_prefs.delete()
            description = 'Server version deleted'
        else:
            description = 'Server version already deleted'

        await utils.send_embed(interaction, description=description, ephemeral=True)


class BibleAdminGroup(app_commands.Group, name='admin'):
    service_manager: ServiceManager

    async def _service_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=service_name, value=service_name)
            for service_name in self.service_manager.service_map.keys()
            if current.lower() in service_name.lower()
        ][:25]

    @app_commands.command()
    @app_commands.describe(version='The Bible version to get information for')
    @app_commands.autocomplete(version=_version_autocomplete)
    async def bibleinfo(
        self, interaction: discord.Interaction, /, version: str
    ) -> None:
        '''Get information for a Bible version'''

        existing = await BibleVersion.get_by_command(version)

        await utils.send_embed(
            interaction,
            title=existing.name,
            fields=[
                {'name': 'Command', 'value': existing.command},
                {'name': 'Abbreviation', 'value': existing.abbr},
                {'name': 'Right to left', 'value': 'Yes' if existing.rtl else 'No'},
                {
                    'name': 'Books',
                    'value': '\n'.join(
                        [name for name in _book_names_from_book_mask(existing.books)]
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
    @app_commands.autocomplete(service=_service_autocomplete)
    async def addbible(
        self,
        interaction: discord.Interaction,
        /,
        command: str,
        name: str,
        abbreviation: str,
        service: str,
        service_version: str,
        books: str = 'OT,NT',
        rtl: bool = False,
    ) -> None:
        '''Add a Bible version'''

        if service not in self.service_manager:
            await utils.send_embed_error(
                interaction,
                description=f'`{service}` is not a valid service',
            )
            return

        try:
            bible = await BibleVersion.create(
                command=command,
                name=name,
                abbr=abbreviation,
                service=service,
                service_version=service_version,
                rtl=rtl,
                books=_book_mask_from_books(books),
            )
            _bible_info.add(bible)  # type: ignore
        except UniqueViolationError:
            await utils.send_embed_error(
                interaction,
                description=f'`{command}` already exists',
            )
        else:
            await utils.send_embed(
                interaction,
                description=f'Added `{command}` as "{name}"',
                color=discord.Colour.green(),
            )

    @app_commands.command()
    @app_commands.describe(version='The version to delete')
    @app_commands.autocomplete(version=_version_autocomplete)
    async def deletebible(
        self, interaction: discord.Interaction, /, version: str
    ) -> None:
        '''Delete a Bible'''

        existing = await BibleVersion.get_by_command(version)
        await existing.delete()

        await utils.send_embed(
            interaction,
            description=f'Removed `{existing.command}`',
        )

    @app_commands.command()
    @app_commands.describe(
        version='The version to update',
        service='Service to use for lookup and search',
        service_version="The service's code for this version",
    )
    @app_commands.autocomplete(
        version=_version_autocomplete, service=_service_autocomplete
    )
    async def updatebible(
        self,
        interaction: discord.Interaction,
        /,
        version: str,
        name: str | None = None,
        abbreviation: str | None = None,
        service: str | None = None,
        service_version: str | None = None,
        rtl: bool | None = None,
        books: str | None = None,
    ) -> None:
        '''Update a Bible'''

        if service is not None and service not in self.service_manager:
            await utils.send_embed_error(
                interaction,
                description=f'`{service}` is not a valid service',
            ),
            return

        bible = await BibleVersion.get_by_command(version)

        try:
            args: dict[str, Any] = {}

            if name is not None:
                args['name'] = name

            if abbreviation is not None:
                args['abbr'] = abbreviation

            if service is not None:
                args['service'] = service

            if service_version is not None:
                args['service_version'] = service_version

            if rtl is not None:
                args['rtl'] = rtl

            if books is not None:
                args['books'] = _book_mask_from_books(books)

            await bible.update(**args).apply()
            _bible_info.update(bible)  # type: ignore

        except Exception:
            await utils.send_embed_error(
                interaction, description=f'Error updating `{version}`'
            )
        else:
            await utils.send_embed(interaction, description=f'Updated `{version}`')


_shared_cooldown = app_commands.checks.cooldown(
    rate=8, per=60.0, key=lambda i: (i.guild_id, i.user.id)
)


class BibleAppCommands(BibleBase):
    admin = admin_guild_only(BibleAdminGroup())
    preferences = PreferencesGroup()

    def __init__(self, bot: Erasmus, service_manager: ServiceManager, /) -> None:
        super().__init__(bot, service_manager)

        self.admin.service_manager = service_manager

    async def cog_load(self) -> None:
        _bible_info.set(
            [  # type: ignore
                version async for version in BibleVersion.get_all(ordered=True)
            ]
        )

    async def cog_unload(self) -> None:
        _bible_info.clear()

    async def cog_app_command_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        /,
    ) -> None:
        if (
            isinstance(
                error, (app_commands.CommandInvokeError, app_commands.TransformerError)
            )
            and error.__cause__ is not None
        ):
            error = cast(Exception, error.__cause__)

        match error:
            case BookNotUnderstoodError():
                message = f'I do not understand the book "{error.book}"'
            case BookNotInVersionError():
                message = f'{error.version} does not contain {error.book}'
            case DoNotUnderstandError():
                message = 'I do not understand that request'
            case ReferenceNotUnderstoodError():
                message = f'I do not understand the reference "{error.reference}"'
            case BibleNotSupportedError():
                message = f'The version `{error.version}` is not supported'
            case NoUserVersionError():
                message = 'You must first set your default version with `/version set`'
            case InvalidVersionError():
                message = (
                    f'`{error.version}` is not a valid version. Check '
                    '`/versions` for valid versions'
                )
            case ServiceNotSupportedError():
                message = (
                    f'The service configured for "{error.bible.name}" is not supported'
                )
            case ServiceLookupTimeout():
                message = (
                    f'The request timed out looking up {error.verses} in '
                    + error.bible.name
                )
            case ServiceSearchTimeout():
                message = (
                    f'The request timed out searching for '
                    f'"{" ".join(error.terms)}" in {error.bible.name}'
                )
            case _:
                return

        await utils.send_embed_error(interaction, description=message)

    @app_commands.command()
    @_shared_cooldown
    @app_commands.describe(
        reference='A verse reference',
        version='The version in which to look up the verse',
        only_me='Whether to display the verse to yourself or everyone',
    )
    @app_commands.autocomplete(version=_version_autocomplete)
    async def verse(
        self,
        interaction: discord.Interaction,
        /,
        reference: VerseRange,
        version: str | None = None,
        only_me: bool = False,
    ) -> None:
        '''Look up a verse'''

        bible: BibleVersion | None = None

        if version is not None:
            reference.version = version

        if reference.version is not None:
            bible = await BibleVersion.get_by_abbr(reference.version)

        if bible is None:
            bible = await BibleVersion.get_for_user(interaction.user, interaction.guild)

        if reference.book_mask == 'DC' or not (bible.books & reference.book_mask):
            raise BookNotInVersionError(reference.book, bible.name)

        await interaction.response.defer(thinking=True, ephemeral=only_me)
        passage = await self.service_manager.get_passage(cast(Any, bible), reference)
        await send_passage(interaction, passage, ephemeral=only_me)

    @app_commands.command()
    @_shared_cooldown
    @app_commands.describe(
        terms='Terms to search for', version='The Bible version to search within'
    )
    @app_commands.autocomplete(version=_version_autocomplete)
    async def search(
        self,
        interaction: discord.Interaction,
        /,
        terms: str,
        version: str | None = None,
    ) -> None:
        '''Search in the Bible'''

        bible: BibleVersion | None = None

        if version is not None:
            bible = await BibleVersion.get_by_abbr(version)

        if bible is None:
            bible = await BibleVersion.get_for_user(interaction.user, interaction.guild)

        async def search(*, per_page: int, page_number: int) -> SearchResults:
            return await self.service_manager.search(
                bible.as_bible(), terms.split(' '), limit=per_page, offset=page_number
            )

        source = SearchPageSource(search, per_page=5, bible=bible.as_bible())
        view = InteractionUIPages(source, interaction=interaction)
        await view.start()

    @app_commands.command()
    @app_commands.checks.cooldown(
        rate=2, per=30.0, key=lambda i: (i.guild_id, i.user.id)
    )
    async def bibles(self, interaction: discord.Interaction, /) -> None:
        '''List which Bible versions are available for lookup and search'''

        lines = ['I support the following Bible versions:', '']

        lines += [f'  `{version.command}`: {version.name}' for version in _bible_info]

        output = '\n'.join(lines)
        await utils.send_embed(interaction, description=output)

    @app_commands.command()
    @_shared_cooldown
    @app_commands.describe(version='The Bible version to get information for')
    @app_commands.autocomplete(version=_version_autocomplete)
    async def bibleinfo(
        self, interaction: discord.Interaction, /, version: str
    ) -> None:
        '''Get information about a Bible version'''

        existing = await BibleVersion.get_by_command(version)

        await utils.send_embed(
            interaction,
            title=existing.name,
            fields=[
                {
                    'name': 'Abbreviation',
                    'value': existing.command,
                },
                {
                    'name': 'Books',
                    'value': '\n'.join(
                        [name for name in _book_names_from_book_mask(existing.books)]
                    ),
                    'inline': False,
                },
            ],
        )


async def setup(bot: Erasmus, /) -> None:
    service_manager = ServiceManager.from_config(bot.config, bot.session)

    await bot.add_cog(Bible(bot, service_manager))
    # await bot.add_cog(BibleAppCommands(bot, service_manager))

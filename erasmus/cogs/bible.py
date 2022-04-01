from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any, Final, cast
from typing_extensions import Self

import discord
from botus_receptus import Cog, checks, formatting, util
from botus_receptus.app_commands import admin_guild_only
from botus_receptus.db import UniqueViolationError
from discord import app_commands
from discord.ext import commands

from ..context import Context
from ..data import Passage, SearchResults, VerseRange, get_book_data
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
from ..utils import send_context_passage, send_interaction_passage


def _book_mask_from_books(books: str, /) -> int:
    book_mask = 0

    for book in books.split(','):
        book = book.strip()
        if book == 'OT':
            book = 'Genesis'
        elif book == 'NT':
            book = 'Matthew'

        book_data = get_book_data(book)
        book_mask = book_mask | book_data['section']

    return book_mask


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
        ctx: Context,
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

    async def cog_command_error(self, ctx: Context, error: Exception, /) -> None:  # type: ignore  # noqa: B950
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

        await util.send_context_error(
            ctx, description=formatting.escape(message, mass_mentions=True)
        )

    @commands.command(
        aliases=[''],
        brief='Look up a verse in your preferred version',
        help=_lookup_help,
    )
    async def lookup(self, ctx: Context, /, *, reference: VerseRange) -> None:
        bible = await BibleVersion.get_for_user(ctx.author, ctx.guild)

        async with ctx.typing():
            await self.__lookup(ctx, bible, reference)

    @commands.command(
        aliases=['s'],
        brief='Search for terms in your preferred version',
        help=_search_help,
    )
    async def search(self, ctx: Context, /, *terms: str) -> None:
        bible = await BibleVersion.get_for_user(ctx.author, ctx.guild)

        await self.__search(ctx, bible, *terms)

    @commands.command(
        brief='List which Bible versions are available for lookup and search'
    )
    @commands.cooldown(rate=2, per=30.0, type=commands.BucketType.channel)
    async def versions(self, ctx: Context, /) -> None:
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
        await util.send_context(ctx, description=f'\n{output}\n')

    @commands.command(brief='Set your preferred version', help=_setversion_help)
    @commands.cooldown(rate=2, per=60.0, type=commands.BucketType.user)
    async def setversion(self, ctx: Context, version: str, /) -> None:
        version = version.lower()
        if version[0] == ctx.prefix:
            version = version[1:]

        existing = await BibleVersion.get_by_command(version)
        await existing.set_for_user(ctx.author)

        await util.send_context(ctx, description=f'Version set to `{version}`')

    @commands.command(brief='Delete your preferred version', help=_unsetversion_help)
    @commands.cooldown(rate=2, per=60.0, type=commands.BucketType.user)
    async def unsetversion(self, ctx: Context, /) -> None:
        user_prefs = await UserPref.get(ctx.author.id)

        if user_prefs is not None:
            await user_prefs.delete()
            await util.send_context(ctx, description='Preferred version deleted')
        else:
            await util.send_context(
                ctx, description='Preferred version already deleted'
            )

    @commands.command(brief='Set the guild default version', help=_setguildversion_help)
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.cooldown(rate=2, per=60.0, type=commands.BucketType.user)
    async def setguildversion(self, ctx: Context, version: str, /) -> None:
        assert ctx.guild is not None

        version = version.lower()
        if version[0] == ctx.prefix:
            version = version[1:]

        existing = await BibleVersion.get_by_command(version)
        await existing.set_for_guild(ctx.guild)

        await util.send_context(ctx, description=f'Guild version set to `{version}`')

    @commands.command(
        brief='Delete the guild default version', help=_unsetguildversion_help
    )
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.cooldown(rate=2, per=60.0, type=commands.BucketType.user)
    async def unsetguildversion(self, ctx: Context, /) -> None:
        assert ctx.guild is not None

        if (guild_prefs := await GuildPref.get(ctx.guild.id)) is not None:
            await guild_prefs.delete()
            await util.send_context(ctx, description='Guild version deleted')
        else:
            await util.send_context(ctx, description='Guild version already deleted')

    @commands.command(name='addbible')
    @checks.dm_only()
    @commands.is_owner()
    async def add_bible(
        self,
        ctx: Context,
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
            await util.send_context_error(
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
            await util.send_context_error(
                ctx, description=f'`{command}` already exists'
            )
        else:
            self.__add_bible_commands(command, name)
            await util.send_context(ctx, description=f'Added `{command}` as "{name}"')

    @commands.command(name='delbible')
    @checks.dm_only()
    @commands.is_owner()
    async def delete_bible(self, ctx: Context, command: str, /) -> None:
        version = await BibleVersion.get_by_command(command)
        await version.delete()

        self.__remove_bible_commands(command)

        await util.send_context(ctx, description=f'Removed `{command}`')

    @commands.command(name='upbible')
    @checks.dm_only()
    @commands.is_owner()
    async def update_bible(
        self,
        ctx: Context,
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
            await util.send_context_error(
                ctx, description=f'Error updating `{command}`'
            )
        else:
            await util.send_context(ctx, description=f'Updated `{command}`')

    async def __version_lookup(self, ctx: Context, /, *, reference: VerseRange) -> None:
        bible = await BibleVersion.get_by_command(cast(str, ctx.invoked_with))

        async with ctx.typing():
            await self.__lookup(ctx, bible, reference)

    async def __version_search(self, ctx: Context, /, *terms: str) -> None:
        bible = await BibleVersion.get_by_command(cast(str, ctx.invoked_with)[1:])

        await self.__search(ctx, bible, *terms)

    async def __lookup(
        self,
        ctx: Context,
        bible: BibleVersion,
        reference: VerseRange,
        /,
    ) -> None:
        if not (bible.books & reference.book_mask):
            raise BookNotInVersionError(reference.book, bible.name)

        if reference is not None:
            passage = await self.service_manager.get_passage(
                cast(Any, bible), reference
            )
            await send_context_passage(ctx, passage)
        else:
            await util.send_context_error(
                ctx, description=f'I do not understand the request `${reference}`'
            )

    async def __search(self, ctx: Context, bible: BibleVersion, /, *terms: str) -> None:
        if not terms:
            await util.send_context_error(
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
        )
        lookup.cog = self
        search = commands.Command(
            Bible.__version_search,
            name=f's{command}',
            brief=f'Search in {name}',
            help=_version_search_help.format(prefix='{prefix}', command=f's{command}'),
            hidden=True,
        )
        search.cog = self

        # Share cooldown across commands
        lookup._buckets = search._buckets = self._user_cooldown

        self.bot.add_command(lookup)  # type: ignore
        self.bot.add_command(search)  # type: ignore

    def __remove_bible_commands(self, command: str, /) -> None:
        self.bot.remove_command(command)
        self.bot.remove_command(f's{command}')


async def is_administrator(interaction: discord.Interaction, /) -> bool:
    if interaction.channel is None or interaction.guild is None:
        raise commands.NoPrivateMessage()

    channel = interaction.channel

    if isinstance(channel, discord.PartialMessageable):
        channel = await interaction.client.fetch_channel(channel.id)

    if isinstance(channel, discord.abc.PrivateChannel):
        raise commands.NoPrivateMessage()

    permissions = channel.permissions_for(cast(discord.Member, interaction.user))

    if not permissions.administrator:
        raise commands.MissingPermissions(['administrator'])

    return True


class GuildVersion(app_commands.Group, name='guildversion'):
    @app_commands.command()
    @app_commands.describe(version='Bible version')
    @app_commands.checks.has_permissions(administrator=True)
    async def set(
        self,
        interaction: discord.Interaction,
        /,
        version: str,
    ) -> None:
        '''Set the default version for the guild (admin-only)'''

        assert interaction.guild is not None

        version = version.lower()

        existing = await BibleVersion.get_by_command(version)
        await existing.set_for_guild(interaction.guild)

        await util.send_interaction(
            interaction,
            description=f'Guild version set to `{version}`',
            ephemeral=True,
        )

    @app_commands.command()
    @app_commands.checks.has_permissions(administrator=True)
    async def delete(self, interaction: discord.Interaction, /) -> None:
        '''Delete the default version for the guild (admin-only)'''

        assert interaction.guild is not None

        if (guild_prefs := await GuildPref.get(interaction.guild.id)) is not None:
            await guild_prefs.delete()
            description = 'Guild version deleted'
        else:
            description = 'Guild version already deleted'

        await util.send_interaction(
            interaction, description=description, ephemeral=True
        )


async def _version_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    return [
        app_commands.Choice(name=bible.name, value=bible.command)
        async for bible in BibleVersion.get_all(ordered=True, search_term=current)
    ]


class UserVersion(app_commands.Group, name='version'):
    @app_commands.command(name='set')
    @app_commands.checks.cooldown(
        rate=2, per=60.0, key=lambda i: (i.guild_id, i.user.id)
    )
    @app_commands.autocomplete(version=_version_autocomplete)
    async def set(
        self,
        interaction: discord.Interaction,
        /,
        version: str,
    ) -> None:
        '''Set your preferred version'''
        version = version.lower()

        existing = await BibleVersion.get_by_command(version)
        await existing.set_for_user(interaction.user)

        await util.send_interaction(
            interaction,
            description=f'Version set to `{version}`',
            ephemeral=True,
        )

    @app_commands.command(name='delete')
    @app_commands.checks.cooldown(
        rate=2, per=60.0, key=lambda i: (i.guild_id, i.user.id)
    )
    async def delete(self, interaction: discord.Interaction, /) -> None:
        '''Delete your preferred version'''
        user_prefs = await UserPref.get(interaction.user.id)

        if user_prefs is not None:
            await user_prefs.delete()
            description = 'Preferred version deleted'
        else:
            description = 'Preferred version already deleted'

        await util.send_interaction(
            interaction, description=description, ephemeral=True
        )


class BibleAdmin(app_commands.Group, name='bible'):
    service_manager: ServiceManager

    async def _service_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=service_name, value=service_name)
            for service_name in self.service_manager.service_map.keys()
            if current.lower() in service_name.lower()
        ]

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
    async def add(
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
            await util.send_interaction_error(
                interaction,
                description=f'`{service}` is not a valid service',
            )
            return

        try:
            await BibleVersion.create(
                command=command,
                name=name,
                abbr=abbreviation,
                service=service,
                service_version=service_version,
                rtl=rtl,
                books=_book_mask_from_books(books),
            )
        except UniqueViolationError:
            await util.send_interaction_error(
                interaction,
                description=f'`{command}` already exists',
            )
        else:
            await util.send_interaction(
                interaction,
                description=f'Added `{command}` as "{name}"',
                color=discord.Colour.green(),
            )

    @app_commands.command()
    @app_commands.describe(version='The version to delete')
    @app_commands.autocomplete(version=_version_autocomplete)
    async def delete(self, interaction: discord.Interaction, /, version: str) -> None:
        '''Delete a Bible'''

        existing = await BibleVersion.get_by_command(version)
        await existing.delete()

        await util.send_interaction(
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
    async def update(
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
            await util.send_interaction_error(
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
        except Exception:
            await util.send_interaction_error(
                interaction, description=f'Error updating `{version}`'
            )
        else:
            await util.send_interaction(interaction, description=f'Updated `{version}`')


_shared_cooldown = app_commands.checks.cooldown(
    rate=8, per=60.0, key=lambda i: (i.guild_id, i.user.id)
)


class BibleAppCommands(BibleBase):
    bible_admin = admin_guild_only(BibleAdmin())
    guildversion = GuildVersion(description='Guild version commands')
    version = UserVersion(description='Bible version commands')

    def __init__(self, bot: Erasmus, service_manager: ServiceManager, /) -> None:
        super().__init__(bot, service_manager)

        self.bible_admin.service_manager = service_manager

    async def cog_app_command_error(
        self,
        interaction: discord.Interaction,
        command: app_commands.Command[Self, ..., Any],
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

        await util.send_interaction_error(interaction, description=message)

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
    @_shared_cooldown
    @app_commands.describe(
        reference='A verse reference',
        version='The version in which to look up the verse',
        only_me='Whether to display the verse to yourself or everyone',
    )
    @app_commands.autocomplete(version=_version_autocomplete)
    async def lookup(
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

        if not (bible.books & reference.book_mask):
            raise BookNotInVersionError(reference.book, bible.name)

        await interaction.response.defer(thinking=True, ephemeral=only_me)
        passage = await self.service_manager.get_passage(cast(Any, bible), reference)
        await send_interaction_passage(interaction, passage, ephemeral=only_me)

    @app_commands.command()
    @app_commands.checks.cooldown(rate=2, per=30.0, key=lambda i: i.channel_id)
    async def versions(self, interaction: discord.Interaction, /) -> None:
        '''List which Bible versions are available for lookup and search'''

        lines = ['I support the following Bible versions:', '']

        lines += [
            f'  `{version.command}`: {version.name}'
            async for version in BibleVersion.get_all(ordered=True)
        ]

        output = '\n'.join(lines)
        await util.send_interaction(interaction, description=output)


async def setup(bot: Erasmus, /) -> None:
    service_manager = ServiceManager.from_config(bot.config, bot.session)

    await bot.add_cog(Bible(bot, service_manager))
    await bot.add_cog(BibleAppCommands(bot, service_manager))

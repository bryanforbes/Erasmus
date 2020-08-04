from __future__ import annotations

from functools import partial
from typing import Any, Dict, List, Optional, Tuple, cast

import discord
from attr import attrib, dataclass
from botus_receptus import Cog, checks, formatting
from botus_receptus.db import UniqueViolationError
from botus_receptus.interactive_pager import FieldPageSource, InteractiveFieldPager
from discord.ext import commands

from ..context import Context
from ..data import Passage, SearchResults, VerseRange, get_book, get_book_mask
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
    ServiceTimeout,
)
from ..service_manager import ServiceManager


@dataclass(slots=True)
class SearchPageSource(FieldPageSource[Passage]):
    search_func: Any
    cache: Dict[int, List[Passage]] = attrib(init=False, factory=dict)

    async def get_page_items(self, page: int) -> List[Passage]:
        if page in self.cache:
            return self.cache[page]

        results: SearchResults = await self.search_func(
            offset=(page - 1) * self.per_page
        )

        self.cache[page] = results.verses

        return results.verses

    def format_field(self, index: int, entry: Passage) -> Tuple[str, str]:
        return str(entry.range), entry.text

    @staticmethod
    def create(
        initial_results: SearchResults, search_func: Any, per_page: int
    ) -> SearchPageSource:
        source = SearchPageSource(
            search_func=search_func,
            total=initial_results.total,
            per_page=per_page,
            show_entry_count=True,
        )

        if len(initial_results.verses) == initial_results.total:
            for page in range(0, source.max_pages):
                page_start = page * per_page
                source.cache[page + 1] = initial_results.verses[
                    page_start : page_start + per_page
                ]
        else:
            source.cache[1] = initial_results.verses

        return source


lookup_help = '''
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

search_help = '''
Arguments:
----------
    [terms...] - One or more terms to search for

Example:
--------
    {prefix}s faith hope

NOTE: Before this command will work, you MUST set your prefered Bible version
      using {prefix}setversion'''

setversion_help = '''
Arguments:
----------
    <version> - A supported version identifier listed in {prefix}versions

Example:
--------
    {prefix}setversion nasb'''

unsetversion_help = '''

Example:
--------
    {prefix}unsetversion'''

setguildversion_help = '''
Arguments:
----------
    <version> - A supported version identifier listed in {prefix}versions

Example:
--------
    {prefix}setguildversion nasb'''

unsetguildversion_help = '''

Example:
--------
    {prefix}unsetguildversion'''

version_lookup_help = '''
Arguments:
----------
    <reference> - A verse reference in one of the following forms:
        Book 1:1
        Book 1:1-2
        Book 1:1-2:1

Example:
--------
    {prefix}{command} John 1:50-2:1'''


version_search_help = '''
Arguments:
----------
    [terms...] - One or more terms to search for

Example:
--------
    {prefix}{command} faith hope'''


class Bible(Cog[Context]):
    def __init__(self, bot: Erasmus) -> None:
        self.bot = bot

        self.service_manager = ServiceManager.from_config(bot.config, bot.session)
        self._user_cooldown = commands.CooldownMapping.from_cooldown(
            8, 60.0, commands.BucketType.user
        )

        # Share cooldown across commands
        self.lookup._buckets = self.search._buckets = self._user_cooldown

    def __pre_inject__(self, bot: commands.Bot[Context]) -> None:
        self.bot.loop.run_until_complete(self.__init())

    async def __init(self) -> None:
        async for version in BibleVersion.get_all():
            self.__add_bible_commands(version.command, version.name)

    async def lookup_from_message(self, ctx: Context, message: discord.Message) -> None:
        bucket = self._user_cooldown.get_bucket(ctx.message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            raise commands.CommandOnCooldown(bucket, retry_after)

        verse_ranges = VerseRange.get_all_from_string(
            message.content, only_bracketed=not self.bot.user.mentioned_in(message)
        )

        if len(verse_ranges) == 0:
            return

        async with ctx.typing():
            user_bible = await BibleVersion.get_for_user(
                ctx.author.id, ctx.guild.id if ctx.guild is not None else None
            )

            for i, verse_range in enumerate(verse_ranges):
                if i > 0:
                    bucket.update_rate_limit()

                bible: Optional[BibleVersion] = None

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

    async def cog_command_error(self, ctx: Context, error: Exception) -> None:
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

        if isinstance(error, BookNotUnderstoodError):
            message = f'I do not understand the book "{error.book}"'
        elif isinstance(error, BookNotInVersionError):
            message = f'{error.version} does not contain {error.book}'
        elif isinstance(error, DoNotUnderstandError):
            message = 'I do not understand that request'
        elif isinstance(error, ReferenceNotUnderstoodError):
            message = f'I do not understand the reference "{error.reference}"'
        elif isinstance(error, BibleNotSupportedError):
            message = f'`{ctx.prefix}{error.version}` is not supported'
        elif isinstance(error, NoUserVersionError):
            message = (
                f'You must first set your default version with `{ctx.prefix}setversion`'
            )
        elif isinstance(error, InvalidVersionError):
            message = (
                f'`{error.version}` is not a valid version. Check '
                f'`{ctx.prefix}versions` for valid versions'
            )
        elif isinstance(error, ServiceNotSupportedError):
            message = (
                f'The service configured for '
                f'`{self.bot.default_prefix}{ctx.invoked_with}` is not supported'
            )
        elif isinstance(error, ServiceTimeout):
            if isinstance(error, ServiceLookupTimeout):
                message = (
                    f'The request timed out looking up {error.verses} in '
                    + error.bible.name
                )
            elif isinstance(error, ServiceSearchTimeout):
                message = (
                    f'The request timed out searching for '
                    f'"{" ".join(error.terms)}" in {error.bible.name}'
                )
        else:
            return

        await ctx.send_error(formatting.escape(message, mass_mentions=True))

    @commands.command(
        aliases=[''],
        brief='Look up a verse in your preferred version',
        help=lookup_help,
    )
    async def lookup(self, ctx: Context, *, reference: VerseRange) -> None:
        bible = await BibleVersion.get_for_user(
            ctx.author.id, ctx.guild.id if ctx.guild is not None else None
        )

        async with ctx.typing():
            await self.__lookup(ctx, bible, reference)

    @commands.command(
        aliases=['s'],
        brief='Search for terms in your preferred version',
        help=search_help,
    )
    async def search(self, ctx: Context, *terms: str) -> None:
        bible = await BibleVersion.get_for_user(
            ctx.author.id, ctx.guild.id if ctx.guild is not None else None
        )

        await self.__search(ctx, bible, *terms)

    @commands.command(
        brief='List which Bible versions are available for lookup and search'
    )
    @commands.cooldown(rate=2, per=30.0, type=commands.BucketType.channel)
    async def versions(self, ctx: Context) -> None:
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
        await ctx.send_embed(f'\n{output}\n')

    @commands.command(brief='Set your preferred version', help=setversion_help)
    @commands.cooldown(rate=2, per=60.0, type=commands.BucketType.user)
    async def setversion(self, ctx: Context, version: str) -> None:
        version = version.lower()
        if version[0] == ctx.prefix:
            version = version[1:]

        existing = await BibleVersion.get_by_command(version)
        await existing.set_for_user(ctx.author.id)

        await ctx.send_embed(f'Version set to `{version}`')

    @commands.command(brief='Delete your preferred version', help=unsetversion_help)
    @commands.cooldown(rate=2, per=60.0, type=commands.BucketType.user)
    async def unsetversion(self, ctx: Context) -> None:
        user_prefs = await UserPref.get(ctx.author.id)

        if user_prefs is not None:
            await user_prefs.delete()
            await ctx.send_embed('Preferred version deleted')
        else:
            await ctx.send_embed('Preferred version already deleted')

    @commands.command(brief='Set the guild default version', help=setguildversion_help)
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.cooldown(rate=2, per=60.0, type=commands.BucketType.user)
    async def setguildversion(self, ctx: Context, version: str) -> None:
        assert ctx.guild is not None

        version = version.lower()
        if version[0] == ctx.prefix:
            version = version[1:]

        existing = await BibleVersion.get_by_command(version)
        await existing.set_for_guild(ctx.guild.id)

        await ctx.send_embed(f'Guild version set to `{version}`')

    @commands.command(
        brief='Delete the guild default version', help=unsetguildversion_help
    )
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.cooldown(rate=2, per=60.0, type=commands.BucketType.user)
    async def unsetguildversion(self, ctx: Context) -> None:
        assert ctx.guild is not None

        if (guild_prefs := await GuildPref.get(ctx.guild.id)) is not None:
            await guild_prefs.delete()
            await ctx.send_embed('Guild version deleted')
        else:
            await ctx.send_embed('Guild version already deleted')

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
    ) -> None:
        if service not in self.service_manager:
            await ctx.send_error(f'`{service}` is not a valid service')
            return

        try:
            book_mask = 0
            for book in books.split(','):
                book = book.strip()
                if book == 'OT':
                    book = 'Genesis'
                elif book == 'NT':
                    book = 'Matthew'

                book_mask = book_mask | get_book_mask(get_book(book))

            await BibleVersion.create(
                command=command,
                name=name,
                abbr=abbr,
                service=service,
                service_version=service_version,
                rtl=rtl,
                books=book_mask,
            )
        except UniqueViolationError:
            await ctx.send_error(f'`{command}` already exists')
        else:
            self.__add_bible_commands(command, name)
            await ctx.send_embed(f'Added `{command}` as "{name}"')

    @commands.command(name='delbible')
    @checks.dm_only()
    @commands.is_owner()
    async def delete_bible(self, ctx: Context, command: str) -> None:
        version = await BibleVersion.get_by_command(command)
        await version.delete()

        self.__remove_bible_commands(command)

        await ctx.send_embed(f'Removed `{command}`')

    @commands.command(name='upbible')
    @checks.dm_only()
    @commands.is_owner()
    async def update_bible(
        self, ctx: Context, command: str, service: str, service_version: str
    ) -> None:
        version = await BibleVersion.get_by_command(command)

        try:
            await version.update(
                service=service, service_version=service_version
            ).apply()
        except Exception:
            await ctx.send_error(f'Error updating `{command}`')
        else:
            await ctx.send_embed(f'Updated `{command}`')

    async def __version_lookup(self, ctx: Context, *, reference: VerseRange) -> None:
        bible = await BibleVersion.get_by_command(cast(str, ctx.invoked_with))

        async with ctx.typing():
            await self.__lookup(ctx, bible, reference)

    async def __version_search(self, ctx: Context, *terms: str) -> None:
        bible = await BibleVersion.get_by_command(cast(str, ctx.invoked_with)[1:])

        await self.__search(ctx, bible, *terms)

    async def __lookup(
        self, ctx: Context, bible: BibleVersion, reference: VerseRange
    ) -> None:
        if not (bible.books & reference.book_mask):
            raise BookNotInVersionError(reference.book, bible.name)

        if reference is not None:
            passage = await self.service_manager.get_passage(
                cast(Any, bible), reference
            )
            await ctx.send_passage(passage)
        else:
            await ctx.send_error(f'I do not understand the request `${reference}`')

    async def __search(self, ctx: Context, bible: BibleVersion, *terms: str) -> None:
        if not terms:
            await ctx.send_error('Please include some terms to search for')
            return

        search = partial(self.service_manager.search, bible, list(terms), limit=5)
        async with ctx.typing():
            initial_results: SearchResults = await search(offset=0)

        if initial_results.total > 0:
            source = SearchPageSource.create(initial_results, search, 5)
            paginator = InteractiveFieldPager.create(ctx, source)
            await paginator.paginate()
        else:
            await ctx.send_embed('I found 0 results')

    def __add_bible_commands(self, command: str, name: str) -> None:
        lookup = self.bot.command(
            name=command,
            brief=f'Look up a verse in {name}',
            help=version_lookup_help.format(prefix='{prefix}', command=command),
            hidden=True,
        )(Bible.__version_lookup)
        lookup.cog = self
        search = self.bot.command(
            name=f's{command}',
            brief=f'Search in {name}',
            help=version_search_help.format(prefix='{prefix}', command=f's{command}'),
            hidden=True,
        )(Bible.__version_search)
        search.cog = self

        # Share cooldown across commands
        lookup._buckets = search._buckets = self._user_cooldown

    def __remove_bible_commands(self, command: str) -> None:
        self.bot.remove_command(command)
        self.bot.remove_command(f's{command}')


def setup(bot: Erasmus) -> None:
    bot.add_cog(Bible(bot))

from __future__ import annotations

from typing import cast, Optional

import attr
import discord
from discord.ext import commands
from botus_receptus.formatting import pluralizer
from botus_receptus.db import UniqueViolationError
from botus_receptus import checks

from ..db.bible import BibleVersion
from ..data import VerseRange, get_book, get_book_mask
from ..service_manager import ServiceManager
from ..exceptions import BookNotInVersionError
from ..erasmus import Erasmus
from ..context import Context

pluralize_match = pluralizer('match', 'es')


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


@attr.s(slots=True, auto_attribs=True)
class Bible(object):
    bot: Erasmus
    service_manager: ServiceManager = attr.ib(init=False)
    _user_cooldown: commands.CooldownMapping = attr.ib(init=False)

    def __attrs_post_init__(self) -> None:
        self.service_manager = ServiceManager.from_config(
            self.bot.config, self.bot.session
        )
        self._user_cooldown = commands.CooldownMapping(
            commands.Cooldown(rate=8, per=60.0, type=commands.BucketType.user)
        )

        # Share cooldown across commands
        self.lookup._buckets = self.search._buckets = self._user_cooldown

        self.bot.loop.run_until_complete(self._init())

    async def _init(self) -> None:
        async for version in BibleVersion.get_all():
            self._add_bible_commands(version.command, version.name)

    async def lookup_from_message(self, ctx: Context, message: discord.Message) -> None:
        verse_ranges = VerseRange.get_all_from_string(
            message.content,
            only_bracketed=not cast(discord.ClientUser, self.bot.user).mentioned_in(
                message
            ),
        )

        if len(verse_ranges) == 0:
            return

        async with ctx.typing():
            user_bible = await BibleVersion.get_for_user(ctx.author.id)

            for verse_range in verse_ranges:
                bible: Optional[BibleVersion] = None

                try:
                    if isinstance(verse_range, Exception):
                        raise verse_range

                    if verse_range.version is not None:
                        bible = await BibleVersion.get_by_abbr(verse_range.version)

                    if bible is None:
                        bible = user_bible

                    await self._lookup(ctx, bible, verse_range)
                except Exception as exc:
                    await self.bot.on_command_error(ctx, exc)

    @commands.command(
        aliases=[''],
        brief='Look up a verse in your preferred version',
        help=lookup_help,
    )
    async def lookup(self, ctx: Context, *, reference: VerseRange) -> None:
        bible = await BibleVersion.get_for_user(ctx.author.id)

        async with ctx.typing():
            await self._lookup(ctx, bible, reference)

    @commands.command(
        aliases=['s'],
        brief='Search for terms in your preferred version',
        help=search_help,
    )
    async def search(self, ctx: Context, *terms: str) -> None:
        bible = await BibleVersion.get_for_user(ctx.author.id)

        await self._search(ctx, bible, *terms)

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
            book_list = books.split(',')
            for book in book_list:
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
            self._add_bible_commands(command, name)
            await ctx.send_embed(f'Added `{command}` as "{name}"')

    @commands.command(name='delbible')
    @checks.dm_only()
    @commands.is_owner()
    async def delete_bible(self, ctx: Context, command: str) -> None:
        version = await BibleVersion.get_by_command(command)
        await version.delete()

        self._remove_bible_commands(command)

        await ctx.send_embed(f'Removed `{command}`')

    async def _version_lookup(self, ctx: Context, *, reference: VerseRange) -> None:
        bible = await BibleVersion.get_by_command(cast(str, ctx.invoked_with))

        async with ctx.typing():
            await self._lookup(ctx, bible, reference)

    async def _version_search(self, ctx: Context, *terms: str) -> None:
        bible = await BibleVersion.get_by_command(cast(str, ctx.invoked_with)[1:])

        await self._search(ctx, bible, *terms)

    async def _lookup(
        self, ctx: Context, bible: BibleVersion, reference: VerseRange
    ) -> None:
        if not (bible.books & reference.book_mask):
            raise BookNotInVersionError(reference.book, bible.name)

        if reference is not None:
            passage = await self.service_manager.get_passage(bible, reference)
            await ctx.send_passage(passage)
        else:
            await ctx.send_error(f'I do not understand the request `${reference}`')

    async def _search(self, ctx: Context, bible: BibleVersion, *terms: str) -> None:
        async with ctx.typing():
            results = await self.service_manager.search(bible, list(terms))
            matches = pluralize_match(results.total)
            output = f'I have found {matches} to your search'

            if results.total > 0:
                verses = '\n'.join([f'- {verse}' for verse in results.verses])
                if results.total <= 20:
                    output = f'{output}:\n\n{verses}'
                else:
                    limit = pluralize_match(20)
                    output = f'{output}. Here are the first {limit}:\n\n{verses}'

            await ctx.send_embed(output)

    def _add_bible_commands(self, command: str, name: str) -> None:
        lookup = self.bot.command(
            name=command,
            brief=f'Look up a verse in {name}',
            help=version_lookup_help.format(prefix='{prefix}', command=command),
            hidden=True,
        )(self._version_lookup)
        search = self.bot.command(
            name=f's{command}',
            brief=f'Search in {name}',
            help=version_search_help.format(prefix='{prefix}', command=f's{command}'),
            hidden=True,
        )(self._version_search)

        # Share cooldown across commands
        lookup._buckets = search._buckets = self._user_cooldown

    def _remove_bible_commands(self, command: str) -> None:
        self.bot.remove_command(command)
        self.bot.remove_command(f's{command}')


def setup(bot: Erasmus) -> None:
    bot.add_cog(Bible(bot))

from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from ..db import (
    select_all, get_bibles, get_bible, get_user_bible, set_user_bible,
    add_bible, delete_bible, UniqueViolationError
)
from ..data import VerseRange
from ..format import pluralizer
from ..service_manager import ServiceManager, Bible as BibleObject
from ..exceptions import OnlyDirectMessage, BookNotInVersionError

if TYPE_CHECKING:
    from ..erasmus import Erasmus  # noqa: F401
    from ..context import Context  # noqa: F401

pluralize_match = pluralizer('match', 'es')


def dm_only():
    def predicate(ctx: 'Context'):
        if not isinstance(ctx.channel, discord.DMChannel):
            raise OnlyDirectMessage('This command can only be used in private messags.')
        return True

    return commands.check(predicate)


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

NOTE: Before this command will work, you MUST set your prefered Bible version using {prefix}setversion'''

search_help = '''
Arguments:
----------
    [terms...] - One or more terms to search for

Example:
--------
    {prefix}s faith hope

NOTE: Before this command will work, you MUST set your prefered Bible version using {prefix}setversion'''

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


class Bible(object):
    __slots__ = ('bot', 'service_manager', '_user_cooldown')

    bot: 'Erasmus'
    service_manager: ServiceManager
    _user_cooldown: commands.CooldownMapping

    def __init__(self, bot: 'Erasmus') -> None:
        self.bot = bot
        self.service_manager = ServiceManager(self.bot.config)
        self._user_cooldown = commands.CooldownMapping(
            commands.Cooldown(rate=8, per=60.0, type=commands.BucketType.user))

        # Share cooldown across commands
        self.lookup._buckets = self.search._buckets = self._user_cooldown

        self.bot.loop.run_until_complete(self._init())

    async def _init(self) -> None:
        async with self.bot.pool.acquire() as db:
            versions = await select_all(db, table='bible_versions')
            for version in versions:
                self._add_bible_commands(version['command'], version['name'])

    @commands.command(aliases=[''],
                      brief='Look up a verse in your preferred version',
                      help=lookup_help)
    async def lookup(self, ctx: 'Context', *, reference: VerseRange) -> None:
        bible = await get_user_bible(ctx.db, ctx.author.id)

        await self._lookup(ctx, bible, reference)

    @commands.command(aliases=['s'],
                      brief='Search for terms in your preferred version',
                      help=search_help)
    async def search(self, ctx: 'Context', *terms: str) -> None:
        bible = await get_user_bible(ctx.db, ctx.author.id)

        await self._search(ctx, bible, *terms)

    @commands.command(brief='List which Bible versions are available for lookup and search')
    @commands.cooldown(rate=2, per=30.0, type=commands.BucketType.channel)
    async def versions(self, ctx: 'Context') -> None:
        lines = ['I support the following Bible versions:', '']

        versions = await get_bibles(ctx.db, ordered=True)
        lines += [f'  `{ctx.prefix}{version["command"]}`: {version["name"]}' for version in versions]

        lines.append("\nYou can search any version by prefixing the version command with 's' "
                     f'(ex. `{ctx.prefix}sesv terms...`)')

        output = '\n'.join(lines)
        await ctx.send_embed(f'\n{output}\n')

    @commands.command(brief='Set your preferred version', help=setversion_help)
    @commands.cooldown(rate=2, per=60.0, type=commands.BucketType.user)
    async def setversion(self, ctx: 'Context', version: str) -> None:
        version = version.lower()
        if version[0] == ctx.prefix:
            version = version[1:]

        existing = await get_bible(ctx.db, version)
        await set_user_bible(ctx.db, ctx.author.id, existing)

        await ctx.send_embed(f'Version set to `{version}`')

    @commands.command(name='addbible')
    @dm_only()
    @commands.is_owner()
    async def add_bible(self, ctx: 'Context', command: str, name: str, abbr: str, service: str,
                        service_version: str, books: int = 3, rtl: bool = False) -> None:
        if service not in self.service_manager:
            await ctx.send_error(f'`{service}` is not a valid service')
            return

        try:
            await add_bible(ctx.db,
                            command=command,
                            name=name,
                            abbr=abbr,
                            service=service,
                            service_version=service_version,
                            rtl=rtl,
                            books=books)
        except UniqueViolationError:
            await ctx.send_error(f'`{command}` already exists')
        else:
            self._add_bible_commands(command, name)
            await ctx.send_embed(f'Added `{command}` as "{name}"')

    @commands.command(name='delbible')
    @dm_only()
    @commands.is_owner()
    async def delete_bible(self, ctx: 'Context', command: str) -> None:
        await get_bible(ctx.db, command)
        await delete_bible(ctx.db, command)

        self._remove_bible_commands(command)

        await ctx.send_embed(f'Removed `{command}`')

    async def _version_lookup(self, ctx: 'Context', *, reference: VerseRange) -> None:
        bible = await get_bible(ctx.db, ctx.invoked_with)

        await self._lookup(ctx, bible, reference)

    async def _version_search(self, ctx: 'Context', *terms: str) -> None:
        bible = await get_bible(ctx.db, ctx.invoked_with[1:])

        await self._search(ctx, bible, *terms)

    async def _lookup(self, ctx: 'Context', bible: BibleObject, reference: VerseRange) -> None:
        if not (bible['books'] & reference.book_mask):
            raise BookNotInVersionError(reference.book, bible['name'])

        if reference is not None:
            async with ctx.typing():
                passage = await self.service_manager.get_passage(bible, reference)
                await ctx.send_passage(passage)
        else:
            await ctx.send_error('I do not understand that request')

    async def _search(self, ctx: 'Context', bible: BibleObject, *terms: str) -> None:
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
        lookup = self.bot.command(name=command,
                                  brief=f'Look up a verse in {name}',
                                  help=version_lookup_help.format(prefix='{prefix}',
                                                                  command=command),
                                  hidden=True)(self._version_lookup)
        search = self.bot.command(name=f's{command}',
                                  brief=f'Search in {name}',
                                  help=version_search_help.format(prefix='{prefix}',
                                                                  command=f's{command}'),
                                  hidden=True)(self._version_search)

        # Share cooldown across commands
        lookup._buckets = search._buckets = self._user_cooldown

    def _remove_bible_commands(self, command: str) -> None:
        self.bot.remove_command(command)
        self.bot.remove_command(f's{command}')


def setup(bot: 'Erasmus') -> None:
    bot.add_cog(Bible(bot))

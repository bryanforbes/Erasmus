from typing import cast

import discord
import re

from asyncpgsa import pg
from asyncpg.exceptions import UniqueViolationError
from configparser import ConfigParser

from discord.ext import commands
from .data import VerseRange
from .service_manager import ServiceManager
from .exceptions import (
    DoNotUnderstandError, BibleNotSupportedError, ServiceNotSupportedError,
    BookNotUnderstoodError, ReferenceNotUnderstoodError
)
from .format import pluralizer
from .context import Context
from .db import bible_versions, guild_bibles, guild_prefs

number_re = re.compile(r'^\d+$')
pluralize_match = pluralizer('match', 'es')

guild_bible_select = bible_versions.select() \
    .select_from(bible_versions.join(guild_bibles))


async def get_guild_prefix(bot: 'Erasmus', message: discord.Message) -> str:
    prefix = None

    if message.guild:
        query = guild_prefs.select() \
            .where(guild_prefs.c.guild_id == message.guild.id)
        prefix = await pg.fetchval(query, column=1)

    if not prefix:
        return bot.default_prefix

    return prefix


class OnlyDirectMessage(commands.CheckFailure):
    pass


def dm_only():
    def predicate(ctx: Context):
        if not isinstance(ctx.channel, discord.DMChannel):
            raise OnlyDirectMessage('This command can only be used in private messags.')
        return True

    return commands.check(predicate)


class Erasmus(commands.Bot):
    default_prefix: str
    service_manager: ServiceManager
    config: ConfigParser

    def __init__(self, config_path: str, *args, **kwargs) -> None:
        self.config = ConfigParser(default_section='erasmus')
        self.config.read(config_path)

        self.default_prefix = self.config.get('erasmus', 'command_prefix', fallback='$')
        self.service_manager = ServiceManager(self.config)

        kwargs['command_prefix'] = get_guild_prefix

        super().__init__(*args, **kwargs)

        self.add_command(self.versions)
        self.add_command(self.add_bible)
        self.add_command(self.delete_bible)

    def run(self, *args, **kwargs) -> None:
        self.loop.run_until_complete(pg.init(
            self.config.get('erasmus', 'db_url'),
            min_size=1,
            max_size=10
        ))

        super().run(self.config.get('erasmus', 'discord_api_key'))

    async def close(self) -> None:
        await pg.pool.close()
        await super().close()

    async def get_context(self, message: discord.Message, *, cls=Context) -> Context:
        return cast(Context, await super().get_context(message, cls=cls))

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        await self.process_commands(message)

    async def process_commands(self, message: discord.Message) -> None:
        ctx = await self.get_context(message)

        if ctx.command is None:
            return

        await self.invoke(ctx)

    async def on_ready(self) -> None:
        async with pg.query(bible_versions.select()) as versions:
            async for version in versions:
                self._add_bible_commands(version.command, version.name)

        await self.change_presence(game=discord.Game(name=f'| {self.default_prefix}versions'))

        print('-----')
        print(f'logged in as {self.user.name} {self.user.id}')

    async def on_command_error(self, ctx: Context, exc: Exception) -> None:
        message = 'An error occurred'
        if isinstance(exc, commands.CommandInvokeError):
            if isinstance(exc.original, BookNotUnderstoodError):
                message = f'I do not understand the book "{exc.original.book}"'
            elif isinstance(exc.original, DoNotUnderstandError):
                message = 'I do not understand that request'
            elif isinstance(exc.original, ReferenceNotUnderstoodError):
                message = f'I do not understand the reference {exc.original.reference}'
            elif isinstance(exc.original, BibleNotSupportedError):
                message = f'{self.default_prefix}{exc.original.version} is not supported'
            elif isinstance(exc.original, ServiceNotSupportedError):
                message = f'The service configured for {self.default_prefix}{ctx.invoked_with} is not supported'
            else:
                print(exc)
                message = 'An error occurred'
        elif isinstance(exc, commands.NoPrivateMessage):
            message = 'This command is not available in private messages'
        elif isinstance(exc, OnlyDirectMessage):
            message = 'This command is only available in private messages'
        elif isinstance(exc, commands.MissingRequiredArgument):
            message = f'The required argument `{exc.param}` is missing'
        else:
            print(exc)

        await ctx.send_error_to_author(message)

    async def on_guild_available(self, guild: discord.Guild) -> None:
        await self.on_guild_join(guild)

    async def on_guild_join(self, guild: discord.Guild) -> None:
        prefs = await pg.fetchrow(guild_prefs.select().where(guild_prefs.c.guild_id == guild.id))

        if not prefs:
            await pg.execute(guild_prefs.insert().values(guild_id=guild.id, prefix=self.default_prefix))
            # await pg.execute(guild_bibles.insert().values(guild_id=guild.id, bible_id=1))
            # await pg.execute(guild_bibles.insert().values(guild_id=guild.id, bible_id=2))
            # await pg.execute(guild_bibles.insert().values(guild_id=guild.id, bible_id=4))
            # await pg.execute(guild_bibles.insert().values(guild_id=guild.id, bible_id=5))
            # await pg.execute(guild_bibles.insert().values(guild_id=guild.id, bible_id=7))

    @commands.command()
    async def versions(self, ctx: Context) -> None:
        lines = ['I support the following Bible versions:', '']

        async with pg.query(bible_versions.select()
                            .order_by(bible_versions.c.command.asc())) as versions:
            lines += [f'  `{ctx.prefix}{version.command}`: {version.name}' async for version in versions]

        lines.append("\nYou can search any version by prefixing the version command with 's' "
                     f'(ex. `{ctx.prefix}sesv terms...`)')

        output = '\n'.join(lines)
        await ctx.send_to_author(f'\n{output}\n')

    @commands.command(name='addbible')
    @dm_only()
    @commands.is_owner()
    async def add_bible(self, ctx: Context, command: str, name: str, abbr: str, service: str,
                        service_version: str) -> None:
        if service not in self.service_manager:
            await ctx.send_error_to_author(f'`{service}` is not a valid service')
            return

        try:
            await pg.execute(bible_versions.insert().values(command=command,
                                                            name=name,
                                                            abbr=abbr,
                                                            service=service,
                                                            service_version=service_version))
        except UniqueViolationError:
            await ctx.send_error_to_author(f'`{command}` already exists')
        else:
            self._add_bible_commands(command, name)
            await ctx.send_to_author(f'Added `{command}` as "{name}"')

    @commands.command(name='delbible')
    @dm_only()
    @commands.is_owner()
    async def delete_bible(self, ctx: Context, command: str) -> None:
        existing = await pg.fetchrow(bible_versions.select()
                                     .where(bible_versions.c.command == command))

        if not existing:
            await ctx.send_error_to_author(f'`{command}` doesn\'t exist for this guild')
            return

        await pg.execute(bible_versions.delete()
                         .where(bible_versions.c.command == command))

        self.remove_command(command)
        self.remove_command(f's{command}')

        await ctx.send_to_author(f'Removed `{command}`')

    async def _version_lookup(self, ctx: Context, *, reference: str) -> None:
        bible = await pg.fetchrow(bible_versions.select()
                                  .where(bible_versions.c.command == ctx.invoked_with))

        if not bible:
            return

        verses = VerseRange.from_string(reference)
        if verses is not None:
            async with ctx.typing():
                passage = await self.service_manager.get_passage(bible, verses)
                await ctx.send_passage(passage)
        else:
            await ctx.send_error_to_author('I do not understand that request')

    async def _version_search(self, ctx: Context, *terms) -> None:
        bible = await pg.fetchrow(bible_versions.select()
                                  .where(bible_versions.c.command == ctx.invoked_with[1:]))

        if not bible:
            return

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

            await ctx.send_to_author(output)

    def _add_bible_commands(self, command: str, name: str) -> None:
        self.command(name=command,
                     description=f'Look up a verse in {name}',
                     hidden=True)(self._version_lookup)
        self.command(name=f's{command}',
                     description=f'Search in {name}',
                     hidden=True)(self._version_search)


__all__ = ['Erasmus']

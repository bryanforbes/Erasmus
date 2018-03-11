from typing import cast, Any

import discord
import logging
import aiohttp
import async_timeout
import json

from asyncpg import create_pool
from asyncpg.pool import Pool
from configparser import ConfigParser

from discord.ext import commands
from discord.ext.commands import Group
from .exceptions import (
    DoNotUnderstandError, BibleNotSupportedError, ServiceNotSupportedError,
    BookNotUnderstoodError, ReferenceNotUnderstoodError, OnlyDirectMessage,
    BookNotInVersionError, NoUserVersionError, InvalidVersionError, NoSectionError,
    NoSectionsError, InvalidConfessionError, ServiceTimeout, ServiceLookupTimeout,
    ServiceSearchTimeout
)
from .context import Context
from .format import HelpFormatter
from . import re

# from .db import guild_prefs


# async def get_guild_prefix(bot: 'Erasmus', message: discord.Message) -> str:
#     prefix = None

#     if message.guild:
#         query = guild_prefs.select() \
#             .where(guild_prefs.c.guild_id == message.guild.id)
#         prefix = await pg.fetchval(query, column=1)

#     if not prefix:
#         return bot.default_prefix

#     return prefix

log = logging.getLogger(__name__)

extensions = (
    'erasmus.cogs.bible',
    'erasmus.cogs.confession',
)

_mention_pattern_re = re.compile(
    '@', re.named_group('target')(re.one_or_more(re.ANY_CHARACTER))
)


def remove_mentions(string: str) -> str:
    return _mention_pattern_re.sub('@\u200b\\g<target>', string)


description = '''
Erasmus:
--------

You can look up all verses in a message one of two ways:

* Mention me in the message
* Surround verse references in []
    ex. [John 3:16] or [John 3:16 NASB]

'''


class Erasmus(commands.Bot):
    config: ConfigParser
    default_prefix: str  # noqa
    pool: Pool
    session: aiohttp.ClientSession

    def __init__(self, config_path: str, *args: Any, **kwargs: Any) -> None:
        self.config = ConfigParser(default_section='erasmus')
        self.config.read(config_path)

        self.default_prefix = kwargs['command_prefix'] = self.config.get('erasmus', 'command_prefix', fallback='$')
        kwargs['formatter'] = HelpFormatter()
        kwargs['description'] = description

        # kwargs['command_prefix'] = get_guild_prefix

        super().__init__(*args, **kwargs)

        self.pool = self.loop.run_until_complete(
            create_pool(
                self.config.get('erasmus', 'db_url'),
                min_size=1,
                max_size=10
            )
        )

        self.session = aiohttp.ClientSession(loop=self.loop)

        self.remove_command('help')
        self.add_command(self.help)

        for extension in extensions:
            try:
                self.load_extension(extension)
            except Exception as e:
                log.exception('Failed to load extension %s.', extension)

    def run_with_config(self) -> None:
        self.run(self.config.get('erasmus', 'discord_api_key'))

    async def close(self) -> None:
        await self.pool.close()
        await super().close()
        await self.session.close()

    async def get_context(self, message: discord.Message, *, cls: Any=Context) -> Context:
        return cast(Context, await super().get_context(message, cls=cls))

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        await self.process_commands(message)

    async def process_commands(self, message: discord.Message) -> None:
        ctx = await self.get_context(message)

        if ctx.command is None:
            await self.cogs['Bible'].lookup_from_message(ctx, message)
            return

        async with ctx.acquire():
            await self.invoke(ctx)

    async def on_ready(self) -> None:
        await self.change_presence(activity=discord.Game(name=f'| {self.default_prefix}help'))
        await self._report_guilds()

        user = cast(discord.ClientUser, self.user)
        log.info('Erasmus ready. Logged in as %s %s', user.name, user.id)

    async def on_command_error(self, ctx: Context, exc: Exception) -> None:
        message = 'An error occurred'

        if isinstance(exc, commands.CommandInvokeError):
            exc = exc.original

        if isinstance(exc, BookNotUnderstoodError):
            message = f'I do not understand the book "{exc.book}"'
        if isinstance(exc, BookNotInVersionError):
            message = f'{exc.version} does not contain {exc.book}'
        elif isinstance(exc, DoNotUnderstandError):
            message = 'I do not understand that request'
        elif isinstance(exc, ReferenceNotUnderstoodError):
            message = f'I do not understand the reference "{exc.reference}"'
        elif isinstance(exc, BibleNotSupportedError):
            message = f'`{ctx.prefix}{exc.version}` is not supported'
        elif isinstance(exc, NoUserVersionError):
            message = f'You must first set your default version with `{ctx.prefix}setversion`'
        elif isinstance(exc, InvalidVersionError):
            message = f'`{exc.version}` is not a valid version. Check `{ctx.prefix}versions` for valid versions'
        elif isinstance(exc, InvalidConfessionError):
            message = f'`{exc.confession}` is not a valid confession.'
        elif isinstance(exc, NoSectionError):
            message = f'`{exc.confession}` does not have {"an" if exc.section_type == "article" else "a"}' \
                f'{exc.section_type} `{exc.section}`'
        elif isinstance(exc, NoSectionsError):
            message = f'`{exc.confession}` has no {exc.section_type}'
        elif isinstance(exc, ServiceNotSupportedError):
            message = f'The service configured for `{self.default_prefix}{ctx.invoked_with}` is not supported'
        elif isinstance(exc, commands.NoPrivateMessage):
            message = 'This command is not available in private messages'
        elif isinstance(exc, commands.CommandOnCooldown):
            message = ''
            if exc.cooldown.type == commands.BucketType.user:
                message = f'You have used this command too many times.'
            elif exc.cooldown.type == commands.BucketType.channel:
                message = f'`{ctx.prefix}{ctx.invoked_with}` has been used too many times in this channel.'
            message = f'{message} You can retry again in {exc.retry_after:.2f} seconds.'
        elif isinstance(exc, OnlyDirectMessage):
            message = 'This command is only available in private messages'
        elif isinstance(exc, commands.MissingRequiredArgument):
            message = f'The required argument `{exc.param.name}` is missing'
        elif isinstance(exc, ServiceTimeout):
            if isinstance(exc, ServiceLookupTimeout):
                message = f'The request timed out looking up {exc.verses} in {exc.bible["name"]}'
            elif isinstance(exc, ServiceSearchTimeout):
                message = f'The request timed out searching for "{" ".join(exc.terms)}" in {exc.bible["name"]}'
        elif isinstance(exc, commands.BadArgument):
            if exc.__cause__:
                return await self.on_command_error(ctx, cast(Exception, exc.__cause__))
        else:
            log.exception('Exception occurred in command "%s"\nInvoked by: %s',
                          ctx.command.qualified_name, ctx.message.content,
                          exc_info=exc,
                          stack_info=True)

        await ctx.send_error(remove_mentions(message))

    @commands.command(brief='List commands for this bot or get help for commands')
    @commands.cooldown(rate=2, per=30.0, type=commands.BucketType.channel)
    async def help(self, ctx: Context, *commands: str) -> None:
        bot = ctx.bot
        destination = ctx.message.author if bot.pm_help else ctx.message.channel

        if len(commands) == 0:
            pages = await bot.formatter.format_help_for(ctx, bot)
        else:
            name = commands[0]

            if name[0] == ctx.prefix:
                name = name[1:]

            name = remove_mentions(name)
            command = bot.all_commands.get(name)

            if command is None:
                await destination.send(bot.command_not_found.format(name))
                return

            if len(commands) > 1:
                group = cast(Group, command)
                for key in commands[1:]:
                    try:
                        key = remove_mentions(key)
                        command = group.all_commands.get(key)

                        if command is None:
                            await destination.send(bot.command_not_found.format(key))
                            return
                    except AttributeError:
                        await destination.send(bot.command_has_no_subcommands.format(command, key))
                        return

            pages = await bot.formatter.format_help_for(ctx, command)

        for page in pages:
            await destination.send(page)

    async def _report_guilds(self) -> None:
        token = self.config.get('erasmus', 'dbl_token', fallback='')
        if not token:
            return

        headers = {
            'Content-Type': 'application/json',
            'Authorization': token
        }
        payload = {'server_count': len(self.guilds)}
        user = cast(discord.ClientUser, self.user)

        with async_timeout.timeout(10):
            await self.session.post(f'https://discordbots.org/api/bots/{user.id}/stats',
                                    data=json.dumps(payload, ensure_ascii=True),
                                    headers=headers)

    async def on_guild_available(self, guild: discord.Guild) -> None:
        await self._report_guilds()

    async def on_guild_join(self, guild: discord.Guild) -> None:
        await self._report_guilds()

    async def on_guild_remove(self, guild: discord.Guild) -> None:
        await self._report_guilds()

    # async def on_guild_available(self, guild: discord.Guild) -> None:
    #     await self.on_guild_join(guild)

    # async def on_guild_join(self, guild: discord.Guild) -> None:
    #     prefs = await pg.fetchrow(guild_prefs.select().where(guild_prefs.c.guild_id == guild.id))

    #     if not prefs:
    #         await pg.execute(guild_prefs.insert().values(guild_id=guild.id, prefix=self.default_prefix))
    #         # await pg.execute(guild_bibles.insert().values(guild_id=guild.id, bible_id=1))
    #         # await pg.execute(guild_bibles.insert().values(guild_id=guild.id, bible_id=2))
    #         # await pg.execute(guild_bibles.insert().values(guild_id=guild.id, bible_id=4))
    #         # await pg.execute(guild_bibles.insert().values(guild_id=guild.id, bible_id=5))
    #         # await pg.execute(guild_bibles.insert().values(guild_id=guild.id, bible_id=7))


__all__ = ['Erasmus']

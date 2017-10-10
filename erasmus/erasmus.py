from typing import cast

import discord
import logging

from asyncpgsa import pg  # type: ignore
from configparser import ConfigParser

from discord.ext import commands
from .exceptions import (
    DoNotUnderstandError, BibleNotSupportedError, ServiceNotSupportedError,
    BookNotUnderstoodError, ReferenceNotUnderstoodError, OnlyDirectMessage,
    BookNotInVersionError
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
)

_mention_pattern_re = re.compile(
    '@', re.named_group('target')(re.one_or_more(re.ANY_CHARACTER))
)


class Erasmus(commands.Bot):
    config: ConfigParser
    default_prefix: str  # noqa

    def __init__(self, config_path: str, *args, **kwargs) -> None:
        self.config = ConfigParser(default_section='erasmus')
        self.config.read(config_path)

        self.default_prefix = kwargs['command_prefix'] = self.config.get('erasmus', 'command_prefix', fallback='$')
        kwargs['formatter'] = HelpFormatter()

        # kwargs['command_prefix'] = get_guild_prefix

        super().__init__(*args, **kwargs)

        self.loop.run_until_complete(
            pg.init(
                self.config.get('erasmus', 'db_url'),
                min_size=1,
                max_size=10
            )
        )

        self.remove_command('help')
        self.add_command(self.help)

        for extension in extensions:
            try:
                self.load_extension(extension)
            except Exception as e:
                log.exception('Failed to load extension %s.', extension)

    def run(self, *args, **kwargs) -> None:
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
        await self.change_presence(game=discord.Game(name=f'| {self.default_prefix}help'))

        log.info('Erasmus ready. Logged in as %s %s', self.user.name, self.user.id)

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
            message = f'I do not understand the reference {exc.reference}'
        elif isinstance(exc, BibleNotSupportedError):
            message = f'{ctx.prefix}{exc.version} is not supported'
        elif isinstance(exc, ServiceNotSupportedError):
            message = f'The service configured for {self.default_prefix}{ctx.invoked_with} is not supported'
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
            message = f'The required argument `{exc.param}` is missing'
        elif isinstance(exc, commands.BadArgument):
            if exc.__cause__:
                return await self.on_command_error(ctx, cast(Exception, exc.__cause__))
        else:
            log.exception('Exception occurred in command %s', ctx.command, exc_info=exc)

        await ctx.send_error_to_author(message)

    @commands.command(brief='List commands for this bot or get help for commands')
    @commands.cooldown(rate=2, per=30.0, type=commands.BucketType.channel)
    async def help(self, ctx: Context, *commands: str) -> None:
        bot = ctx.bot
        destination = ctx.message.author if bot.pm_help else ctx.message.channel

        if len(commands) == 0:
            pages = await bot.formatter.format_help_for(ctx, bot)
        elif len(commands) == 1:
            name = commands[0]

            if name[0] == ctx.prefix:
                name = name[1:]

            name = _mention_pattern_re.sub('@\u200b\\g<target>', name)
            command = bot.all_commands.get(name)

            if command is None:
                await destination.send(bot.command_not_found.format(name))
                return

            pages = await bot.formatter.format_help_for(ctx, command)
        else:
            pages = []

        for page in pages:
            await destination.send(page)

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

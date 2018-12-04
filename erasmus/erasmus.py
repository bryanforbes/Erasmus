from __future__ import annotations

from typing import cast, Any

import discord
import logging
import pendulum  # type: ignore

from discord.ext import commands
from discord.ext.commands import Group
from botus_receptus import formatting, checks, DblBot
from botus_receptus.gino import Bot

from .config import Config
from .exceptions import ErasmusError
from .context import Context
from .format import HelpFormatter

log = logging.getLogger(__name__)

extensions = ('bible', 'confession', 'creeds')


description = '''
Erasmus:
--------

You can look up all verses in a message one of two ways:

* Mention me in the message
* Surround verse references in []
    ex. [John 3:16] or [John 3:16 NASB]

'''


class Erasmus(Bot[Context], DblBot[Context]):
    config: Config

    context_cls = Context

    def __init__(self, config: Config, *args: Any, **kwargs: Any) -> None:
        kwargs['formatter'] = HelpFormatter()
        kwargs['description'] = description

        super().__init__(config, *args, verify_ssl=False, **kwargs)

        self.remove_command('help')
        self.add_command(self.help)

        for extension in extensions:
            try:
                self.load_extension(f'erasmus.cogs.{extension}')
            except Exception:
                log.exception('Failed to load extension %s.', extension)

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        await self.process_commands(message)

    async def process_commands(self, message: discord.Message) -> None:
        ctx = await self.get_context(message)

        if ctx.command is None:
            await self.cogs['Bible'].lookup_from_message(ctx, message)
            return

        await self.invoke(ctx)

    async def on_ready(self) -> None:
        await super().on_ready()
        await self.change_presence(
            activity=discord.Game(name=f'| {self.default_prefix}help')
        )

        user = cast(discord.ClientUser, self.user)
        log.info('Erasmus ready. Logged in as %s %s', user.name, user.id)

    async def on_command_error(self, ctx: Context, exc: Exception) -> None:
        if (
            isinstance(
                exc,
                (
                    commands.CommandInvokeError,
                    commands.BadArgument,
                    commands.ConversionError,
                ),
            )
            and exc.__cause__ is not None
        ):
            exc = cast(Exception, exc.__cause__)

        if isinstance(exc, ErasmusError):
            # All of these are handled in their respective cogs
            return

        message = 'An error occurred'

        if isinstance(exc, commands.NoPrivateMessage):
            message = 'This command is not available in private messages'
        elif isinstance(exc, commands.CommandOnCooldown):
            message = ''
            if exc.cooldown.type == commands.BucketType.user:
                message = f'You have used this command too many times.'
            elif exc.cooldown.type == commands.BucketType.channel:
                message = (
                    f'`{ctx.prefix}{ctx.invoked_with}` has been used too many '
                    'times in this channel.'
                )
            retry_period = pendulum.now().add(seconds=int(exc.retry_after)).diff()
            message = f'{message} You can retry again in {retry_period.in_words()}.'
        elif isinstance(exc, checks.OnlyDirectMessage):
            message = 'This command is only available in private messages'
        elif isinstance(exc, commands.MissingRequiredArgument):
            message = f'The required argument `{exc.param.name}` is missing'
        else:
            if ctx.command is None:
                qualified_name = 'NO COMMAND'
            else:
                qualified_name = ctx.command.qualified_name

            if ctx.message is None:
                content = 'NO MESSAGE'
            else:
                content = ctx.message.content

            log.exception(
                'Exception occurred in command "%s"\nInvoked by: %s',
                qualified_name,
                content,
                exc_info=exc,
                stack_info=True,
            )

        await ctx.send_error(formatting.escape(message, mass_mentions=True))

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

            name = formatting.escape(name, mass_mentions=True)
            command = bot.all_commands.get(name)

            if command is None:
                await destination.send(bot.command_not_found.format(name))
                return

            if len(commands) > 1:
                group = cast(Group, command)
                for key in commands[1:]:
                    try:
                        key = formatting.escape(key, mass_mentions=True)
                        command = group.all_commands.get(key)

                        if command is None:
                            await destination.send(bot.command_not_found.format(key))
                            return
                    except AttributeError:
                        await destination.send(
                            bot.command_has_no_subcommands.format(command, key)
                        )
                        return

            pages = await bot.formatter.format_help_for(ctx, command)

        for page in pages:
            await destination.send(page)


__all__ = ['Erasmus']

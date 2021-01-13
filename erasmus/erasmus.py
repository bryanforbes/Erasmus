from __future__ import annotations

import logging
from typing import Any, Final, cast

import discord
import pendulum
from botus_receptus import DblBot, abc, exceptions, formatting
from botus_receptus.gino import Bot as GinoBot
from botus_receptus.interactive_pager import CannotPaginate, CannotPaginateReason
from discord.ext import commands, menus

from .config import Config
from .context import Context
from .db import db
from .exceptions import ErasmusError
from .help import HelpCommand

_log: Final = logging.getLogger(__name__)

_extensions: Final = ('bible', 'confession', 'creeds', 'misc')


_description: Final = '''
Erasmus:
--------

You can look up all verses in a message one of two ways:

* Mention me in the message
* Surround verse references in []
    ex. [John 3:16] or [John 3:16 NASB]

'''


class Erasmus(
    GinoBot[Context],
    DblBot[Context],
    abc.OnMessage,
    abc.OnCommandError[Context],
):
    config: Config

    context_cls = Context
    db = db

    def __init__(self, config: Config, *args: Any, **kwargs: Any) -> None:
        kwargs['help_command'] = HelpCommand(
            paginator=formatting.Paginator(),
            command_attrs={
                'brief': 'List commands for this bot or get help for commands',
                'cooldown': commands.Cooldown(5, 30.0, commands.BucketType.channel),
            },
        )
        kwargs['description'] = _description
        kwargs['intents'] = discord.Intents(guilds=True, reactions=True, messages=True)

        super().__init__(config, *args, **kwargs)

        for extension in _extensions:
            try:
                self.load_extension(f'erasmus.cogs.{extension}')
            except Exception:
                _log.exception('Failed to load extension %s.', extension)

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

        user = self.user
        _log.info('Erasmus ready. Logged in as %s %s', user.name, user.id)

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
                message = 'You have used this command too many times.'
            elif exc.cooldown.type == commands.BucketType.channel:
                message = (
                    f'`{ctx.prefix}{ctx.invoked_with}` has been used too many '
                    'times in this channel.'
                )
            retry_period: pendulum.Period = (
                pendulum.now().add(seconds=int(exc.retry_after)).diff()  # type: ignore
            )
            message = (
                f'{message} You can retry again in '  # type: ignore
                f'{retry_period.in_words()}.'
            )
        elif isinstance(exc, commands.MissingPermissions):
            message = 'You do not have the correct permissions to run this command'
        elif isinstance(exc, exceptions.OnlyDirectMessage):
            message = 'This command is only available in private messages'
        elif isinstance(exc, commands.MissingRequiredArgument):
            message = f'The required argument `{exc.param.name}` is missing'
        elif isinstance(exc, CannotPaginate):
            if exc.reason == CannotPaginateReason.embed_links:
                message = 'I need the "Embed Links" permission'
            elif exc.reason == CannotPaginateReason.send_messages:
                message = 'I need the "Send Messages" permission'
            elif exc.reason == CannotPaginateReason.add_reactions:
                message = 'I need the "Add Reactions" permission'
            elif exc.reason == CannotPaginateReason.read_message_history:
                message = 'I need the "Read Message History" permission'
        elif isinstance(exc, menus.CannotSendMessages):
            message = 'I need the "Send Messages" permission'
        elif isinstance(exc, menus.CannotEmbedLinks):
            message = 'I need the "Embed Links" permission'
        elif isinstance(exc, menus.CannotAddReactions):
            message = 'I need the "Add Reactions" permission'
        elif isinstance(exc, menus.CannotReadMessageHistory):
            message = 'I need the "Read Message History" permission'
        else:
            if ctx.command is None:
                qualified_name = 'NO COMMAND'
            else:
                qualified_name = ctx.command.qualified_name

            if ctx.message is None:
                content = 'NO MESSAGE'
            else:
                content = ctx.message.content

            _log.exception(
                'Exception occurred in command "%s"\nInvoked by: %s',
                qualified_name,
                content,
                exc_info=exc,
                stack_info=True,
            )

        await ctx.send_error(formatting.escape(message, mass_mentions=True))


__all__: Final = ['Erasmus']

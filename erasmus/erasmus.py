from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Final, cast

import discord
import pendulum
from botus_receptus import exceptions, formatting, gino, topgg, utils
from botus_receptus.interactive_pager import CannotPaginate, CannotPaginateReason
from discord import app_commands
from discord.ext import commands
from pendulum.period import Period

from .config import Config
from .context import Context
from .db import db
from .exceptions import ErasmusError
from .help import HelpCommand

if TYPE_CHECKING:
    from .cogs.bible import Bible

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
    gino.AutoShardedBot,
    topgg.AutoShardedBot,
):
    config: Config

    context_cls = Context
    db = db

    def __init__(self, config: Config, /, *args: Any, **kwargs: Any) -> None:
        kwargs['help_command'] = HelpCommand(
            paginator=formatting.Paginator(),
            command_attrs={
                'brief': 'List commands for this bot or get help for commands',
                'cooldown': commands.CooldownMapping.from_cooldown(
                    5, 30.0, commands.BucketType.user
                ),
            },
        )
        kwargs['description'] = _description
        kwargs['intents'] = discord.Intents(
            guilds=True, reactions=True, messages=True, message_content=True
        )
        kwargs['allowed_mentions'] = discord.AllowedMentions(
            roles=False, everyone=False, users=True
        )

        super().__init__(config, *args, **kwargs)

        self.tree.error(self.on_app_command_error)

    async def setup_hook(self) -> None:
        await super().setup_hook()

        for extension in _extensions:
            try:
                await self.load_extension(f'erasmus.cogs.{extension}')
            except Exception:
                _log.exception('Failed to load extension %s.', extension)

        await self.sync_app_commands()

        _log.info(
            'Global commands: '
            f'{list(self.tree._global_commands.keys())!r}'  # type: ignore
        )

        for guild_id, _commands in self.tree._guild_commands.items():  # type: ignore
            _log.info(f'Commands for {guild_id}: {list(_commands)!r}')  # type: ignore

    async def on_message(self, message: discord.Message, /) -> None:
        if message.author.bot:
            return

        await self.process_commands(message)

    async def process_commands(self, message: discord.Message, /) -> None:
        ctx = await self.get_context(message, cls=Context)

        if ctx.command is None:
            await cast('Bible', self.cogs['Bible']).lookup_from_message(ctx, message)
            return

        await self.invoke(ctx)

    async def on_ready(self, /) -> None:
        await super().on_ready()
        await self.change_presence(
            activity=discord.Game(name=f'| {self.default_prefix}help')
        )

        user = self.user
        assert user is not None
        _log.info('Erasmus ready. Logged in as %s %s', user.name, user.id)

    async def on_command_error(
        self,
        context: commands.Context[Any],
        exception: Exception,
        /,
    ) -> None:
        assert isinstance(context, Context)

        if (
            isinstance(
                exception,
                (
                    commands.CommandInvokeError,
                    commands.BadArgument,
                    commands.ConversionError,
                ),
            )
            and exception.__cause__ is not None
        ):
            exception = cast(commands.CommandError, exception.__cause__)

        if isinstance(exception, ErasmusError):
            # All of these are handled in their respective cogs
            return

        message = 'An error occurred'

        match exception:
            case commands.NoPrivateMessage():
                message = 'This command is not available in private messages'
            case commands.CommandOnCooldown():
                message = ''
                if exception.type == commands.BucketType.user:
                    message = 'You have used this command too many times.'
                elif exception.type == commands.BucketType.channel:
                    message = (
                        f'`{context.prefix}{context.invoked_with}` has been used too '
                        'many times in this channel.'
                    )
                retry_period: Period = (
                    pendulum.now()
                    .add(seconds=int(exception.retry_after))
                    .diff()  # type: ignore
                )
                message = (
                    f'{message} You can retry again in '
                    f'{retry_period.in_words()}.'  # type: ignore
                )
            case commands.MissingPermissions():
                message = 'You do not have the correct permissions to run this command'
            case exceptions.OnlyDirectMessage():
                message = 'This command is only available in private messages'
            case commands.MissingRequiredArgument():
                message = f'The required argument `{exception.param.name}` is missing'
            case CannotPaginate():
                match exception.reason:
                    case CannotPaginateReason.embed_links:
                        message = 'I need the "Embed Links" permission'
                    case CannotPaginateReason.send_messages:
                        message = 'I need the "Send Messages" permission'
                    case CannotPaginateReason.add_reactions:
                        message = 'I need the "Add Reactions" permission'
                    case CannotPaginateReason.read_message_history:
                        message = 'I need the "Read Message History" permission'
            case _:
                if context.command is None:
                    qualified_name = 'NO COMMAND'
                else:
                    qualified_name = context.command.qualified_name

                if context.message is None:
                    content = 'NO MESSAGE'
                else:
                    content = context.message.content

                _log.exception(
                    'Exception occurred in command "%s"\nInvoked by: %s',
                    qualified_name,
                    content,
                    exc_info=exception,
                    stack_info=True,
                )

        await utils.send_embed_error(
            context, description=formatting.escape(message, mass_mentions=True)
        )

    async def on_app_command_error(
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

        if isinstance(error, ErasmusError):
            # All of these are handled in their respective cogs
            return

        message = 'An error occurred'

        match error:
            case commands.NoPrivateMessage():
                message = 'This command is not available in private messages'
            case app_commands.CommandOnCooldown():
                retry_period: Period = (
                    pendulum.now()
                    .add(seconds=int(error.retry_after))
                    .diff()  # type: ignore
                )
                message = (
                    'You have used this command too many times. You can retry again in '
                    f'{retry_period.in_words()}.'  # type: ignore
                )
            case app_commands.MissingPermissions():
                message = 'You do not have permission to run this command'
            case CannotPaginate():
                match error.reason:
                    case CannotPaginateReason.embed_links:
                        message = 'I need the "Embed Links" permission'
                    case CannotPaginateReason.send_messages:
                        message = 'I need the "Send Messages" permission'
                    case CannotPaginateReason.add_reactions:
                        message = 'I need the "Add Reactions" permission'
                    case CannotPaginateReason.read_message_history:
                        message = 'I need the "Read Message History" permission'
            case _:
                if interaction.command is None:
                    qualified_name = 'NO INTERACTION'
                else:
                    command = interaction.command
                    if isinstance(command, app_commands.Command):
                        qualified_name = f'{command.name}'
                        parent = command.parent
                        if parent is not None:
                            qualified_name = f'{parent.name} {qualified_name}'
                            parent_parent = parent.parent
                            if parent_parent is not None:
                                qualified_name = (
                                    f'{parent_parent.name} {qualified_name}'
                                )
                    else:
                        qualified_name = command.name

                _log.exception(
                    'Exception occurred in interaction "%s"',
                    qualified_name,
                    exc_info=error,
                    stack_info=True,
                )

        await utils.send_embed_error(interaction, description=message)


__all__: Final = ('Erasmus',)

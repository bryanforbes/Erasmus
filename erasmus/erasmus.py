from __future__ import annotations

import contextlib
import logging
import sys
from typing import TYPE_CHECKING, Any, Final, cast

import discord
import discord.http
import pendulum
from asyncpg.exceptions import UniqueViolationError
from botus_receptus import exceptions, formatting, sqlalchemy as sa, topgg, utils
from botus_receptus.interactive_pager import CannotPaginate, CannotPaginateReason
from discord import app_commands
from discord.ext import commands
from sqlalchemy import select

from .db import Notification, Session
from .exceptions import ErasmusError
from .help import HelpCommand
from .l10n import Localizer
from .translator import Translator

if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing_extensions import Self

    from .cogs.bible import Bible
    from .config import Config

_log: Final = logging.getLogger(__name__)

_extensions: Final = ('admin', 'bible', 'confession', 'creeds', 'misc')


_description: Final = '''
Erasmus:
--------

You can look up all verses in a message one of two ways:

* Mention me in the message
* Surround verse references in []
    ex. [John 3:16] or [John 3:16 NASB]

'''


discord.http._set_api_version(9)


class Erasmus(sa.AutoShardedBot, topgg.AutoShardedBot):
    config: Config
    slash_command_notifications: set[int]
    localizer: Localizer

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
        kwargs['intents'] = discord.Intents(guilds=True, reactions=True, messages=True)
        kwargs['allowed_mentions'] = discord.AllowedMentions.none()

        self.slash_command_notifications = set()
        self.localizer = Localizer(discord.Locale.american_english)

        super().__init__(config, *args, sessionmaker=Session, **kwargs)

        self.tree.error(self.on_app_command_error)
        self.before_invoke(self.__before_invoke)

    async def _application_command_notice(
        self,
        ctx: commands.Context[Self] | discord.Interaction,
        /,
        *,
        skip_check: bool = False,
    ) -> None:
        if not skip_check and (
            ctx.guild is None or ctx.guild.id in self.slash_command_notifications
        ):
            return

        await utils.send_embed(
            ctx,
            title='Notice of future changes',
            description=(
                f'{formatting.underline(formatting.bold("Users"))}\n'
                'Beginning <t:1661972400:D>, Erasmus will no longer respond to '
                'text-based commands (`$confess` and others) or bracket citations '
                '(`[John 1:1]`). At that time, Discord will require all bots to use '
                'slash commands. All text-based commands have been converted into '
                'slash commands and Erasmus will only respond to bracket citations if '
                'it is mentioned as part of the message text.\n\n'
                'To see a list of commands available, type `/` in the text input '
                'for a server Erasmus is in and select its icon in the popup.\n\n'
                f'{formatting.underline(formatting.bold("Server Moderators"))}\n'
                'In order to allow your users to use the new slash commands, '
                'you should reauthorize Erasmus in your server by doing the '
                'following (**NOTE:** You **do not** have to remove Erasmus from your '
                'server):\n\n'
                '- Click [this link](https://discord.com/api/oauth2/authorize?'
                'client_id=349394562336292876&permissions=274878000192&'
                'scope=applications.commands%20bot)\n'
                '- In the popup that opens, select your server in the drop down and '
                'tap "Continue"\n'
                '- In the popup that opens, tap "Authorize"\n\n'
                'To see this message again, run `/notice`.'
            ),
            color=discord.Color.yellow(),
        )

        if (
            ctx.guild is not None
            and ctx.guild.id not in self.slash_command_notifications
        ):
            self.slash_command_notifications.add(ctx.guild.id)

            with contextlib.suppress(UniqueViolationError):
                async with Session.begin() as session:
                    session.add(
                        Notification(id=ctx.guild.id, application_commands=True)
                    )

    async def __before_invoke(self, ctx: commands.Context[Self], /) -> None:
        try:
            await self._application_command_notice(ctx)
        except Exception as exc:  # noqa: PIE786
            await self.on_command_error(ctx, exc)

    @property
    def bible_cog(self) -> Bible:
        return self.cogs['Bible']  # type: ignore

    async def setup_hook(self) -> None:
        await super().setup_hook()

        async with Session.begin() as session:
            self.slash_command_notifications = {
                notification.id
                for notification in cast(
                    'Iterable[Notification]',
                    await session.scalars(select(Notification)),
                )
            }

        for extension in _extensions:
            try:
                await self.load_extension(f'erasmus.cogs.{extension}')
            except commands.ExtensionError:
                _log.exception('Failed to load extension %s.', extension)

        await self.tree.set_translator(Translator(self.localizer))
        await self.sync_app_commands()

        _log.info(
            'Global commands: '
            f'{list(self.tree._global_commands.keys())!r}'  # type: ignore
        )

        for guild_id, _commands in self.tree._guild_commands.items():  # type: ignore
            _log.info(f'Commands for {guild_id}: {list(_commands)!r}')  # type: ignore

    async def process_commands(self, message: discord.Message, /) -> None:
        if message.author.bot:
            return

        ctx = await self.get_context(message)

        if ctx.command is None:
            try:
                await self.bible_cog.lookup_from_message(ctx, message)
            except commands.CommandError as exc:
                self.dispatch('command_error', ctx, exc)

            return

        await self.invoke(ctx)

    async def on_ready(self, /) -> None:
        await self.change_presence(
            activity=discord.Game(name=f'| {self.default_prefix}help')
        )

        user = self.user
        assert user is not None
        _log.info('Erasmus ready. Logged in as %s %s', user.name, user.id)

        await super().on_ready()

    async def on_error(self, event_method: str, /, *args: Any, **kwargs: Any) -> None:
        _, exception, _ = sys.exc_info()

        if exception is None:
            return

        _log.exception(
            f'Exception occurred handling an event:\n\tEvent: {event_method}',
            exc_info=exception,
            stack_info=True,
        )

    async def on_command_error(
        self, context: commands.Context[Any], exception: Exception, /
    ) -> None:
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
            exception = cast('commands.CommandError', exception.__cause__)

        if isinstance(exception, ErasmusError):
            # All of these are handled in their respective cogs
            return

        message_id = 'generic-error'
        data: dict[str, Any] | None = None

        match exception:
            case commands.NoPrivateMessage():
                message_id = 'no-private-message'
            case commands.CommandOnCooldown():
                if exception.type == commands.BucketType.user:
                    message_id = 'user-on-cooldown'
                elif exception.type == commands.BucketType.channel:
                    message_id = 'command-on-cooldown'
                else:
                    message_id = 'cooldown-error'

                retry_period = (
                    pendulum.now().add(seconds=int(exception.retry_after)).diff()
                )
                data = {'period': retry_period}
            case commands.MissingPermissions():
                message_id = 'missing-permissions'
            case exceptions.OnlyDirectMessage():
                message_id = 'only-private-messages'
            case commands.MissingRequiredArgument():
                message_id = 'missing-required-argument'
                data = {'name': exception.param.name}
            case CannotPaginate():
                match exception.reason:
                    case CannotPaginateReason.embed_links:
                        permission = 'embed-links'
                    case CannotPaginateReason.send_messages:
                        permission = 'send-messages'
                    case CannotPaginateReason.add_reactions:
                        permission = 'add-reactions'
                    case CannotPaginateReason.read_message_history:
                        permission = 'read-message-history'

                message_id = 'cannot-paginate'
                data = {'permission': permission}
            case _:
                qualified_name = (
                    'NO COMMAND'
                    if context.command is None
                    else context.command.qualified_name
                )
                content = (
                    'NO MESSAGE' if context.message is None else context.message.content
                )
                invoked_by = f'{context.author} ({context.author.id})'

                _log.exception(
                    'Exception occurred processing a message:\n'
                    f'\tCommand: {qualified_name}\n'
                    f'\tInvoked by: {invoked_by}\n'
                    f'\tJump URL: {context.message.jump_url}\n'
                    f'\tInvoked with: {content}',
                    exc_info=exception,
                    stack_info=True,
                )

        if not isinstance(exception, discord.errors.Forbidden):
            await utils.send_embed_error(
                context,
                description=formatting.escape(
                    self.localizer.format(
                        message_id,
                        data=data,
                        locale=context.interaction.locale
                        if context.interaction is not None
                        else None,
                    ),
                    mass_mentions=True,
                ),
            )

    async def on_app_command_error(
        self, itx: discord.Interaction, error: Exception, /
    ) -> None:
        if (
            isinstance(
                error, (app_commands.CommandInvokeError, app_commands.TransformerError)
            )
            and error.__cause__ is not None
        ):
            error = cast('Exception', error.__cause__)

        if isinstance(error, ErasmusError):
            # All of these are handled in their respective cogs
            return

        message_id = 'generic-error'
        data: dict[str, Any] | None = None

        match error:
            case commands.NoPrivateMessage():
                message_id = 'no-private-message'
            case app_commands.CommandOnCooldown():
                retry_period = pendulum.now().add(seconds=int(error.retry_after)).diff()

                message_id = 'user-on-cooldown'
                data = {'period': retry_period}
            case app_commands.MissingPermissions():
                message_id = 'missing-permissions'
            case CannotPaginate():
                match error.reason:
                    case CannotPaginateReason.embed_links:
                        permission = 'embed-links'
                    case CannotPaginateReason.send_messages:
                        permission = 'send-messages'
                    case CannotPaginateReason.add_reactions:
                        permission = 'add-reactions'
                    case CannotPaginateReason.read_message_history:
                        permission = 'read-message-history'

                message_id = 'cannot-paginate'
                data = {'permission': permission}
            case _:
                qualified_name = (
                    'NO INTERACTION'
                    if itx.command is None
                    else itx.command.qualified_name
                )
                jump_url = 'NONE' if itx.message is None else itx.message.jump_url
                invoked_by = f'{itx.user} ({itx.user.id})'

                _log.exception(
                    'Exception occurred in interaction:\n'
                    f'\tInteraction: {qualified_name}\n'
                    f'\tInvoked by: {invoked_by}\n'
                    f'\tJump URL: {jump_url}',
                    exc_info=error,
                    stack_info=True,
                )

        if not isinstance(error, discord.errors.Forbidden):
            await utils.send_embed_error(
                itx,
                description=self.localizer.format(
                    message_id, data=data, locale=itx.locale
                ),
            )


__all__: Final = ('Erasmus',)

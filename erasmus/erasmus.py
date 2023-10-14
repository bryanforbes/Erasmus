from __future__ import annotations

import logging
import sys
from functools import cached_property
from importlib import metadata
from typing import TYPE_CHECKING, Final, cast
from typing_extensions import override

import discord
import discord.http
import pendulum
from botus_receptus import sqlalchemy as sa, topgg, utils
from botus_receptus.interactive_pager import CannotPaginate, CannotPaginateReason
from discord import app_commands
from discord.ext import commands

from . import json
from .db import Session
from .exceptions import ErasmusError
from .l10n import Localizer
from .translator import Translator

if TYPE_CHECKING:
    from .cogs.bible import Bible
    from .config import Config

_log: Final = logging.getLogger(__name__)
_extensions: Final = ('admin', 'bible', 'confession', 'creeds', 'misc')
_version: Final = metadata.version('erasmus')


class Erasmus(sa.AutoShardedBot, topgg.AutoShardedBot):
    config: Config  # pyright: ignore[reportIncompatibleVariableOverride]
    localizer: Localizer

    def __init__(self, config: Config, /, *args: object, **kwargs: object) -> None:
        self.localizer = Localizer(discord.Locale.american_english)

        super().__init__(
            config,
            *args,
            sessionmaker=Session,
            engine_kwargs={
                'json_serializer': json.serialize,
                'json_deserializer': json.deserialize,
                'connect_args': {
                    'server_settings': {'timezone': 'utc'},
                },
            },
            help_command=None,
            allowed_mentions=discord.AllowedMentions.none(),
            **kwargs,
        )

        self.tree.error(self.on_app_command_error)

    @cached_property
    def invite_url(self) -> str:
        return discord.utils.oauth_url(
            self.application_id,
            permissions=discord.Permissions(
                add_reactions=True,
                embed_links=True,
                manage_messages=True,
                manage_webhooks=True,
                read_message_history=True,
                read_messages=True,
                send_messages=True,
                send_messages_in_threads=True,
            ),
        )

    @property
    def bible_cog(self) -> Bible:
        return self.cogs['Bible']  # pyright: ignore[reportGeneralTypeIssues]

    @override
    async def setup_hook(self) -> None:
        await super().setup_hook()

        for extension in _extensions:
            try:
                await self.load_extension(f'erasmus.cogs.{extension}')
            except commands.ExtensionError:
                _log.exception('Failed to load extension %s.', extension)

        await self.tree.set_translator(Translator(self.localizer))
        await self.sync_app_commands()

        _log.info(
            'Global commands: '
            f'{list(self.tree._global_commands.keys())!r}'  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
        )

        for (
            guild_id,
            _commands,  # pyright: ignore[reportUnknownVariableType]
        ) in (
            self.tree._guild_commands.items()  # pyright: ignore[reportUnknownMemberType]
        ):
            _log.info(
                f'Commands for {guild_id}: {list(_commands)!r}'  # pyright: ignore[reportUnknownArgumentType]
            )

    @override
    async def on_message(self, message: discord.Message, /) -> None:
        if message.author.bot or not message.content:
            return

        await self.bible_cog.lookup_from_message(message)

    @override
    async def on_ready(self, /) -> None:
        user = self.user
        _log.info('Erasmus ready. Logged in as %s %s', user.name, user.id)

        await super().on_ready()

    async def on_shard_connect(self, shard_id: int, /) -> None:
        _log.info(f'Shard {shard_id + 1} connected')

    async def on_shard_disconnect(self, shard_id: int, /) -> None:
        _log.info(f'Shard {shard_id + 1} disconnected')

    async def on_shard_ready(self, shard_id: int, /) -> None:
        await self.change_presence(
            activity=discord.Game(f'v{_version} | shard {shard_id + 1}'),
            shard_id=shard_id,
        )

        _log.info(f'Shard {shard_id + 1} ready')

    async def on_shard_resumed(self, shard_id: int, /) -> None:
        _log.info(f'Shard {shard_id + 1} resumed')

    @override
    async def on_error(
        self, event_method: str, /, *args: object, **kwargs: object
    ) -> None:
        _, exception, _ = sys.exc_info()

        if exception is None:
            return

        _log.exception(
            f'Exception occurred handling an event:\n\tEvent: {event_method}',
            exc_info=exception,
            stack_info=True,
        )

    async def on_app_command_error(
        self, itx: discord.Interaction | discord.Message, error: Exception, /
    ) -> None:
        if (
            isinstance(
                error,
                app_commands.CommandInvokeError | app_commands.TransformerError,
            )
            and error.__cause__ is not None
        ):
            error = cast(Exception, error.__cause__)

        if isinstance(error, ErasmusError):
            # All of these are handled in their respective cogs
            return

        message_id = 'generic-error'
        data: dict[str, object] | None = None

        match error:
            case commands.NoPrivateMessage():
                message_id = 'no-private-message'
            case app_commands.CommandOnCooldown():
                retry_interval = (
                    pendulum.now().add(seconds=int(error.retry_after)).diff()
                )

                message_id = 'user-on-cooldown'
                data = {'interval': retry_interval}
            case app_commands.MissingPermissions():
                message_id = 'missing-permissions'
            case CannotPaginate():
                match error.reason:
                    case CannotPaginateReason.embed_links:
                        message_id = 'need-permission-embed-links'
                    case CannotPaginateReason.send_messages:
                        message_id = 'need-permission-send-messages'
                    case CannotPaginateReason.add_reactions:
                        message_id = 'need-permission-add-reactions'
                    case CannotPaginateReason.read_message_history:
                        message_id = 'need-permission-read-message-history'
            case _:
                if isinstance(itx, discord.Interaction):
                    action = 'interaction'
                    qualified_name = (
                        'NO INTERACTION'
                        if itx.command is None
                        else itx.command.qualified_name
                    )
                    jump_url = 'NONE' if itx.message is None else itx.message.jump_url
                    invoked_by = f'{itx.user} ({itx.user.id})'
                else:
                    action = 'lookup'
                    qualified_name = 'NO INTERACTION'
                    jump_url = itx.jump_url
                    invoked_by = f'{itx.author} ({itx.author.id})'

                _log.exception(
                    f'Exception occurred in {action}:\n'
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
                    message_id,
                    data=data,
                    locale=itx.locale if isinstance(itx, discord.Interaction) else None,
                ),
            )


__all__: Final = ('Erasmus',)

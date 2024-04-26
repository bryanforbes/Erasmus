from __future__ import annotations

import io
import textwrap
import traceback
from contextlib import asynccontextmanager, redirect_stdout
from typing import TYPE_CHECKING, Any, Final, Self, override

import discord
from botus_receptus import GroupCog, utils
from botus_receptus.app_commands import admin_guild_only
from discord import app_commands

from .. import checks
from ..db import Session
from ..erasmus import Erasmus, _extensions as _extension_names
from ..types import Refreshable

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator

_available_extensions: Final = {f'erasmus.cogs.{name}' for name in _extension_names}


class _EvalError(Exception): ...


class _RunError(Exception):
    value: str
    formatted: str

    def __init__(self, value: str, formatted: str) -> None:
        super().__init__()
        self.value = value
        self.formatted = formatted


class _EvalModal(discord.ui.Modal, title='Evaluate Python Code'):
    _admin: Admin

    code: discord.ui.TextInput[Self] = discord.ui.TextInput(
        label='Code', placeholder='Code here…', style=discord.TextStyle.paragraph
    )

    def __init__(self, admin: Admin, *, timeout: float | None = None) -> None:
        super().__init__(timeout=timeout)

        self._admin = admin

    def _cleanup_code(self, content: str) -> str:
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        # remove `foo`
        return content.strip('` \n')

    @override
    async def on_submit(self, itx: discord.Interaction, /) -> None:
        env: dict[str, Any] = {
            'bot': itx.client,
            'interaction': itx,
            'user': itx.user,
            'channel': itx.channel,
            'guild': itx.guild,
            'message': itx.message,
            '_': self._admin._last_result,
        }

        env.update(globals())

        body = self._cleanup_code(self.code.value)
        stdout = io.StringIO()

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        try:
            exec(to_compile, env)  # noqa: S102
        except Exception as e:
            raise _EvalError from e

        func = env['func']

        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            raise _RunError(stdout.getvalue(), traceback.format_exc()) from e
        else:
            value = stdout.getvalue()

            if ret is None:
                if value:
                    await utils.send(itx, content=f'```py\n{value}\n```')
            else:
                self._admin._last_result = ret
                await utils.send(itx, content=f'```py\n{value}{ret}\n```')

    @override
    async def on_error(self, itx: discord.Interaction, error: Exception, /) -> None:
        if error.__cause__ is not None and isinstance(error, _EvalError):
            await utils.send(
                itx,
                content=f'```py\n{error.__cause__.__class__.__name__}: {error}\n```',
            )
        elif isinstance(error, _RunError):
            await utils.send(itx, content=f'```py\n{error.value}{error.formatted}\n```')
        else:
            await utils.send(
                itx, content=f'```py\n{error.__class__.__name__}: {error}\n```'
            )


@asynccontextmanager
async def operation_guard(
    itx: discord.Interaction, success_message: str, /
) -> AsyncIterator[None]:
    try:
        await itx.response.defer()
        yield
    except Exception as e:  # noqa: BLE001
        await utils.send_embed_error(itx, description=f'{e.__class__.__name__}: {e}')
    else:
        await utils.send_embed(
            itx,
            description=success_message,
            color=discord.Color.green(),
        )


@admin_guild_only()
class Admin(GroupCog[Erasmus], group_name='admin', group_description='Admin commands'):
    _last_result: object

    def __init__(self, bot: Erasmus, /) -> None:
        if bot.config.get('enable_eval', False):
            self._eval = (  # pyright: ignore[reportUnknownMemberType]
                app_commands.command(name='eval')(self.__eval)
            )

            self.__cog_app_commands_group__.add_command(  # pyright: ignore[reportOptionalMemberAccess]
                self._eval  # pyright: ignore[reportUnknownArgumentType, reportUnknownMemberType]
            )

        super().__init__(bot)

    @override
    async def cog_load(self) -> None:
        self._last_result = None

    @checks.is_owner()
    async def __eval(self, itx: discord.Interaction, /) -> None:
        """Evaluates code"""

        await itx.response.send_modal(_EvalModal(self))

    async def __unloaded_modules_autocomplete(
        self, _: discord.Interaction, current: str, /
    ) -> list[app_commands.Choice[str]]:
        loaded_extensions = set(self.bot.extensions.keys())
        return [
            app_commands.Choice(name=extension_name, value=extension_name)
            for extension_name in _available_extensions
            if extension_name not in loaded_extensions
            and current.lower() in extension_name.lower()
        ][:25]

    @app_commands.command()
    @checks.is_owner()
    @app_commands.describe(module='The module to load')
    @app_commands.autocomplete(module=__unloaded_modules_autocomplete)
    async def load(self, itx: discord.Interaction, /, module: str) -> None:
        """Loads an extension module"""

        async with operation_guard(itx, f'`{module}` loaded'):
            await self.bot.load_extension(module)

    @property
    def __loaded_modules(self) -> Iterator[str]:
        yield from [
            extension_name
            for extension_name in sorted(self.bot.extensions.keys())
            if extension_name in _available_extensions
        ]

    async def __loaded_modules_autocomplete(
        self, _: discord.Interaction, current: str, /
    ) -> list[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=extension_name, value=extension_name)
            for extension_name in self.__loaded_modules
            if current.lower() in extension_name.lower()
        ][:25]

    @app_commands.command()
    @checks.is_owner()
    @app_commands.describe(module='The module to reload')
    @app_commands.autocomplete(module=__loaded_modules_autocomplete)
    async def reload(self, itx: discord.Interaction, /, module: str) -> None:
        """Reloads an extension module"""

        async with operation_guard(itx, f'`{module}` reloaded'):
            await self.bot.reload_extension(module)

    async def __loaded_modules_without_admin_autocomplete(
        self, _: discord.Interaction, current: str, /
    ) -> list[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=extension_name, value=extension_name)
            for extension_name in self.__loaded_modules
            if not extension_name.endswith('.admin')
            and current.lower() in extension_name.lower()
        ][:25]

    @app_commands.command()
    @checks.is_owner()
    @app_commands.describe(module='The module to unload')
    @app_commands.autocomplete(module=__loaded_modules_without_admin_autocomplete)
    async def unload(self, itx: discord.Interaction, /, module: str) -> None:
        """Unloads an extension module"""

        async with operation_guard(itx, f'`{module}` unloaded'):
            await self.bot.unload_extension(module)

    @app_commands.command()
    @checks.is_owner()
    async def sync(self, itx: discord.Interaction, /) -> None:
        """Syncs command tree to Discord"""

        async with operation_guard(itx, 'Commands synced'):
            await self.bot.sync_app_commands()

    @app_commands.command(name='refresh-data')
    @checks.is_owner()
    async def refresh_data(self, itx: discord.Interaction, /) -> None:
        """Refresh cached data from the database"""

        async with operation_guard(itx, 'Data refreshed'), Session() as session:
            for cog in self.bot.cogs.values():
                if isinstance(cog, Refreshable):
                    await cog.refresh(session)

    @app_commands.command(name='reload-translations')
    @checks.is_owner()
    async def reload_translations(self, itx: discord.Interaction, /) -> None:
        """Reload translations and sync"""

        async with operation_guard(itx, 'Translations reloaded'):
            with self.bot.localizer.begin_reload():
                await self.bot.sync_app_commands()


async def setup(bot: Erasmus, /) -> None:
    await bot.add_cog(Admin(bot))

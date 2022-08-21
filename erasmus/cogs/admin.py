from __future__ import annotations

import io
import textwrap
import traceback
from contextlib import redirect_stdout
from typing import TYPE_CHECKING, Any, Final

import discord
from botus_receptus import GroupCog, utils
from botus_receptus.app_commands import admin_guild_only
from discord import app_commands
from discord.ext import commands

from .. import checks
from ..erasmus import Erasmus, _extensions as _extension_names

if TYPE_CHECKING:
    from typing_extensions import Self

_available_extensions: Final = {f'erasmus.cogs.{name}' for name in _extension_names}


class _EvalError(Exception):
    ...


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

    async def on_submit(  # pyright: ignore [reportIncompatibleMethodOverride]
        self,
        itx: discord.Interaction,
        /,
    ) -> None:
        assert self.code.value is not None

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
            exec(to_compile, env)
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

    async def on_error(  # pyright: ignore [reportIncompatibleMethodOverride]
        self,
        itx: discord.Interaction,
        error: Exception,
        /,
    ) -> None:
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


@admin_guild_only()
class Admin(GroupCog[Erasmus], group_name='admin', group_description='Admin commands'):
    _last_result: Any

    async def cog_load(self) -> None:
        self._last_result = None

    async def __unloaded_modules_autocomplete(
        self,
        itx: discord.Interaction,
        current: str,
        /,
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
        '''Loads an extension module'''

        try:
            await self.bot.load_extension(module)
        except commands.ExtensionError as e:
            await utils.send_embed_error(
                itx, description=f'{e.__class__.__name__}: {e}'
            )
        else:
            await utils.send_embed(
                itx,
                description=f'`{module}` loaded',
                color=discord.Color.green(),
            )

    async def __loaded_modules_autocomplete(
        self,
        itx: discord.Interaction,
        current: str,
        /,
    ) -> list[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=extension_name, value=extension_name)
            for extension_name in self.bot.extensions.keys()
            if extension_name in _available_extensions
            and current.lower() in extension_name.lower()
        ][:25]

    @app_commands.command()
    @checks.is_owner()
    @app_commands.describe(module='The module to reload')
    @app_commands.autocomplete(module=__loaded_modules_autocomplete)
    async def reload(self, itx: discord.Interaction, /, module: str) -> None:
        '''Reloads an extension module'''

        try:
            await self.bot.reload_extension(module)
        except commands.ExtensionError as e:
            await utils.send_embed_error(
                itx, description=f'{e.__class__.__name__}: {e}'
            )
        else:
            await utils.send_embed(
                itx,
                description=f'`{module}` reloaded',
                color=discord.Color.green(),
            )

    async def __loaded_modules_without_admin_autocomplete(
        self,
        itx: discord.Interaction,
        current: str,
        /,
    ) -> list[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=extension_name, value=extension_name)
            for extension_name in self.bot.extensions.keys()
            if extension_name in _available_extensions
            and not extension_name.endswith('.admin')
            and current.lower() in extension_name.lower()
        ][:25]

    @app_commands.command()
    @checks.is_owner()
    @app_commands.describe(module='The module to unload')
    @app_commands.autocomplete(module=__loaded_modules_without_admin_autocomplete)
    async def unload(self, itx: discord.Interaction, /, module: str) -> None:
        '''Unloads an extension module'''

        try:
            await self.bot.unload_extension(module)
        except commands.ExtensionError as e:
            await utils.send_embed_error(
                itx, description=f'{e.__class__.__name__}: {e}'
            )
        else:
            await utils.send_embed(
                itx,
                description=f'`{module}` unloaded',
                color=discord.Color.green(),
            )

    @app_commands.command()
    @checks.is_owner()
    async def sync(self, itx: discord.Interaction, /) -> None:
        '''Syncs command tree to Discord'''

        try:
            await itx.response.defer()
            await self.bot.sync_app_commands()
        except Exception as e:  # noqa: PIE786
            await utils.send_embed_error(
                itx, description=f'{e.__class__.__name__}: {e}'
            )
        else:
            await utils.send_embed(
                itx,
                description='Commands synced',
                color=discord.Color.green(),
            )

    @app_commands.command(name='eval')
    @checks.is_owner()
    async def _eval(self, itx: discord.Interaction, /) -> None:
        '''Evaluates code'''

        await itx.response.send_modal(_EvalModal(self))


async def setup(bot: Erasmus, /) -> None:
    await bot.add_cog(Admin(bot))

from __future__ import annotations

from typing import Final

import discord
from botus_receptus import Cog, utils
from botus_receptus.app_commands import admin_guild_only
from discord import app_commands
from discord.ext import commands

from .. import checks
from ..erasmus import Erasmus
from ..erasmus import _extensions as _extension_names

_available_extensions: Final = {f'erasmus.cogs.{name}' for name in _extension_names}


class Admin(Cog[Erasmus]):
    admin = admin_guild_only(
        app_commands.Group(name='admin', description='Admin commands')
    )

    async def __unloaded_modules_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        loaded_extensions = set(self.bot.extensions.keys())
        return [
            app_commands.Choice(name=extension_name, value=extension_name)
            for extension_name in _available_extensions
            if extension_name not in loaded_extensions
            and current.lower() in extension_name.lower()
        ][:25]

    @admin.command()
    @checks.is_owner()
    @app_commands.describe(module='The module to load')
    @app_commands.autocomplete(module=__unloaded_modules_autocomplete)
    async def load(self, interaction: discord.Interaction, /, module: str) -> None:
        '''Loads an extension module'''

        try:
            await self.bot.load_extension(module)
        except commands.ExtensionError as e:
            await utils.send_embed_error(
                interaction, description=f'{e.__class__.__name__}: {e}'
            )
        else:
            await utils.send_embed(
                interaction,
                description=f'`{module}` loaded',
                color=discord.Color.green(),
            )

    async def __loaded_modules_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=extension_name, value=extension_name)
            for extension_name in self.bot.extensions.keys()
            if extension_name in _available_extensions
            and current.lower() in extension_name.lower()
        ][:25]

    @admin.command()
    @checks.is_owner()
    @app_commands.describe(module='The module to reload')
    @app_commands.autocomplete(module=__loaded_modules_autocomplete)
    async def reload(self, interaction: discord.Interaction, /, module: str) -> None:
        '''Reloads an extension module'''

        try:
            await self.bot.reload_extension(module)
        except commands.ExtensionError as e:
            await utils.send_embed_error(
                interaction, description=f'{e.__class__.__name__}: {e}'
            )
        else:
            await utils.send_embed(
                interaction,
                description=f'`{module}` reloaded',
                color=discord.Color.green(),
            )

    async def __loaded_modules_without_admin_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=extension_name, value=extension_name)
            for extension_name in self.bot.extensions.keys()
            if extension_name in _available_extensions
            and not extension_name.endswith('.admin')
            and current.lower() in extension_name.lower()
        ][:25]

    @admin.command()
    @checks.is_owner()
    @app_commands.describe(module='The module to unload')
    @app_commands.autocomplete(module=__loaded_modules_without_admin_autocomplete)
    async def unload(self, interaction: discord.Interaction, /, module: str) -> None:
        '''Unloads an extension module'''

        try:
            await self.bot.unload_extension(module)
        except commands.ExtensionError as e:
            await utils.send_embed_error(
                interaction, description=f'{e.__class__.__name__}: {e}'
            )
        else:
            await utils.send_embed(
                interaction,
                description=f'`{module}` unloaded',
                color=discord.Color.green(),
            )

    @admin.command()
    @checks.is_owner()
    async def sync(self, interaction: discord.Interaction, /) -> None:
        '''Syncs command tree to Discord'''

        try:
            await interaction.response.defer()
            await self.bot.sync_app_commands()
        except Exception as e:
            await utils.send_embed_error(
                interaction, description=f'{e.__class__.__name__}: {e}'
            )
        else:
            await utils.send_embed(
                interaction,
                description='Commands synced',
                color=discord.Color.green(),
            )


async def setup(bot: Erasmus, /) -> None:
    await bot.add_cog(Admin(bot))

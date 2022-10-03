from __future__ import annotations

from typing import TYPE_CHECKING

from botus_receptus import utils
from discord import app_commands

from ...db import BibleVersion, GuildPref, Session
from .bible_lookup import bible_lookup  # noqa
from .daily_bread_group import DailyBreadPreferencesGroup

if TYPE_CHECKING:
    import discord

    from ...l10n import Localizer
    from .cog import Bible


@app_commands.default_permissions(administrator=True)
@app_commands.guild_only()
class ServerPreferencesGroup(
    app_commands.Group, name='serverprefs', description='Server preferences'
):
    localizer: Localizer

    daily_bread = DailyBreadPreferencesGroup()

    def initialize_from_cog(self, cog: Bible, /) -> None:
        self.localizer = cog.localizer

        self.daily_bread.initialize_from_cog(cog)

    @app_commands.command()
    @app_commands.describe(version='Bible version')
    @app_commands.checks.cooldown(
        rate=2, per=60.0, key=lambda i: (i.guild_id, i.user.id)
    )
    async def setdefault(
        self,
        itx: discord.Interaction,
        /,
        version: app_commands.Transform[str, bible_lookup],
    ) -> None:
        '''Set the default version for this server'''

        assert itx.guild is not None

        version = version.lower()

        async with Session.begin() as session:
            existing = await BibleVersion.get_by_command(session, version)
            await existing.set_for_guild(session, itx.guild)

        await utils.send_embed(
            itx,
            description=self.localizer.format(
                'serverprefs__setdefault.response',
                data={'version': version},
                locale=itx.locale,
            ),
            ephemeral=True,
        )

    @app_commands.command()
    @app_commands.checks.cooldown(
        rate=2, per=60.0, key=lambda i: (i.guild_id, i.user.id)
    )
    async def unsetdefault(self, itx: discord.Interaction, /) -> None:
        '''Unset the default version for this server'''

        assert itx.guild is not None

        async with Session.begin() as session:
            if (guild_prefs := await session.get(GuildPref, itx.guild.id)) is not None:
                await session.delete(guild_prefs)
                attribute_id = 'deleted'
            else:
                attribute_id = 'already-deleted'

        await utils.send_embed(
            itx,
            description=self.localizer.format(
                f'serverprefs__unsetdefault.{attribute_id}', locale=itx.locale
            ),
            ephemeral=True,
        )

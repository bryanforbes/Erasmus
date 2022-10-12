from __future__ import annotations

from typing import TYPE_CHECKING

from botus_receptus import utils
from discord import app_commands

from ...db import BibleVersion, GuildPref, Session
from .bible_lookup import bible_lookup  # noqa
from .daily_bread import DailyBreadPreferencesGroup

if TYPE_CHECKING:
    import discord

    from ...erasmus import Erasmus
    from ...l10n import GroupLocalizer
    from .types import ParentCog, ParentGroup


class ServerPreferencesVersionGroup(
    app_commands.Group, name='version', description='Server Bible version preferences'
):
    localizer: GroupLocalizer

    def initialize_from_parent(self, parent: ParentGroup, /) -> None:
        self.localizer = parent.localizer.for_group(self)

    @app_commands.command()
    @app_commands.describe(version='Bible version')
    @app_commands.checks.cooldown(
        rate=2, per=60.0, key=lambda i: (i.guild_id, i.user.id)
    )
    async def set(
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
                'set.response',
                data={'version': version},
                locale=itx.locale,
            ),
            ephemeral=True,
        )

    @app_commands.command()
    @app_commands.checks.cooldown(
        rate=2, per=60.0, key=lambda i: (i.guild_id, i.user.id)
    )
    async def clear(self, itx: discord.Interaction, /) -> None:
        '''Clear the default version for this server'''

        assert itx.guild is not None

        async with Session.begin() as session:
            if (
                guild_prefs := await GuildPref.for_guild(session, itx.guild)
            ) is not None:
                await session.delete(guild_prefs)
                attribute_id = 'deleted'
            else:
                attribute_id = 'already-deleted'

        await utils.send_embed(
            itx,
            description=self.localizer.format(
                f'clear.{attribute_id}', locale=itx.locale
            ),
            ephemeral=True,
        )

    @app_commands.command()
    @app_commands.checks.cooldown(
        rate=2, per=60.0, key=lambda i: (i.guild_id, i.user.id)
    )
    async def show(self, itx: discord.Interaction, /) -> None:
        '''Display the default version for this server'''

        assert itx.guild is not None

        async with Session() as session:
            guild_prefs = await GuildPref.for_guild(session, itx.guild)

        if guild_prefs is not None and guild_prefs.bible_version is not None:
            attribute_id = 'set'
            data = {'version': guild_prefs.bible_version.name}
        else:
            attribute_id = 'not-set'
            data = None

        await utils.send_embed(
            itx,
            description=self.localizer.format(
                f'show.{attribute_id}', locale=itx.locale, data=data
            ),
            ephemeral=True,
        )


@app_commands.default_permissions(administrator=True)
@app_commands.guild_only()
class ServerPreferencesGroup(
    app_commands.Group, name='serverprefs', description='Server preferences'
):
    bot: Erasmus
    localizer: GroupLocalizer

    version_group = ServerPreferencesVersionGroup()
    daily_bread = DailyBreadPreferencesGroup()

    def initialize_from_parent(self, parent: ParentCog, /) -> None:
        self.bot = parent.bot
        self.localizer = parent.localizer.for_group(self)

        self.version_group.initialize_from_parent(self)
        self.daily_bread.initialize_from_parent(self)

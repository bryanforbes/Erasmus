from __future__ import annotations

from typing import TYPE_CHECKING

from botus_receptus import utils
from discord import app_commands

from ...db import BibleVersion, Session, UserPref
from .bible_lookup import bible_lookup  # noqa

if TYPE_CHECKING:
    import discord

    from ...l10n import Localizer
    from .cog import Bible


class PreferencesGroup(app_commands.Group, name='prefs', description='Preferences'):
    localizer: Localizer

    def initialize_from_cog(self, cog: Bible, /) -> None:
        self.localizer = cog.localizer

    @app_commands.command()
    @app_commands.describe(version='Bible version')
    @app_commands.checks.cooldown(rate=2, per=60.0, key=lambda i: i.user.id)
    async def setdefault(
        self,
        itx: discord.Interaction,
        /,
        version: app_commands.Transform[str, bible_lookup],
    ) -> None:
        '''Set your default Bible version'''
        version = version.lower()

        async with Session.begin() as session:
            existing = await BibleVersion.get_by_command(session, version)
            await existing.set_for_user(session, itx.user)

        await utils.send_embed(
            itx,
            description=self.localizer.format(
                'prefs__setdefault.response',
                data={'version': version},
                locale=itx.locale,
            ),
            ephemeral=True,
        )

    @app_commands.command()
    @app_commands.checks.cooldown(rate=2, per=60.0, key=lambda i: i.user.id)
    async def unsetdefault(self, itx: discord.Interaction, /) -> None:
        '''Unset your default Bible version'''
        async with Session.begin() as session:
            user_prefs = await UserPref.for_user(session, itx.user)

            if user_prefs is not None:
                await session.delete(user_prefs)
                attribute_id = 'deleted'
            else:
                attribute_id = 'already-deleted'

        await utils.send_embed(
            itx,
            description=self.localizer.format(
                f'prefs__unsetdefault.{attribute_id}', locale=itx.locale
            ),
            ephemeral=True,
        )

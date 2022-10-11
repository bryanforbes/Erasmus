from __future__ import annotations

from typing import TYPE_CHECKING

from botus_receptus import utils
from discord import app_commands

from erasmus.db.bible import GuildPref

from ...db import BibleVersion, Session, UserPref
from .bible_lookup import bible_lookup  # noqa

if TYPE_CHECKING:
    import discord

    from ...l10n import GroupLocalizer
    from .types import ParentCog


class VersionGroup(
    app_commands.Group, name='version', description='Bible version preferences'
):
    localizer: GroupLocalizer

    def initialize_from_parent(self, parent: ParentCog, /) -> None:
        self.localizer = parent.localizer.for_group(self)

    @app_commands.command()
    @app_commands.describe(version='Bible version')
    @app_commands.checks.cooldown(rate=2, per=60.0, key=lambda i: i.user.id)
    async def set(
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
                'set.response',
                data={'version': version},
                locale=itx.locale,
            ),
            ephemeral=True,
        )

    @app_commands.command()
    @app_commands.checks.cooldown(rate=2, per=60.0, key=lambda i: i.user.id)
    async def clear(self, itx: discord.Interaction, /) -> None:
        '''Clear your default Bible version'''

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
                f'clear.{attribute_id}', locale=itx.locale
            ),
            ephemeral=True,
        )

    @app_commands.command()
    @app_commands.checks.cooldown(rate=2, per=60.0, key=lambda i: i.user.id)
    async def show(self, itx: discord.Interaction, /) -> None:
        '''Display your default Bible version preferences'''

        localizer = self.localizer.for_message('show', locale=itx.locale)

        async with Session() as session:
            display_version: BibleVersion | None = None
            user_prefs = await UserPref.for_user(session, itx.user)

            if user_prefs is not None and user_prefs.bible_version is not None:
                display_version = user_prefs.bible_version
                output = localizer.format(
                    'user-set', data={'version': display_version.name}
                )
            else:
                output = localizer.format('user-not-set')

            if itx.guild is not None:
                guild_prefs = await GuildPref.for_guild(session, itx.guild)

                if guild_prefs is not None and guild_prefs.bible_version is not None:
                    guild_output = localizer.format(
                        'guild-set', data={'version': guild_prefs.bible_version.name}
                    )

                    if display_version is None:
                        display_version = guild_prefs.bible_version
                else:
                    guild_output = localizer.format('guild-not-set')

                output = f'{output}\n{guild_output}'

            if display_version is None:
                display_version = await BibleVersion.get_for(session)

            output = f'{output}\n\n' + localizer.format(
                "display-version", data={"version": display_version.name}
            )

        await utils.send_embed(itx, description=output, ephemeral=True)

from __future__ import annotations

from collections import OrderedDict
from importlib import metadata
from pathlib import Path
from typing import TYPE_CHECKING

import discord
from botus_receptus import Cog, Embed, formatting, utils
from discord import app_commands

if TYPE_CHECKING:
    from ..erasmus import Erasmus
    from ..l10n import Localizer, MessageLocalizer


class InviteView(discord.ui.View):
    def __init__(
        self,
        invite_url: str,
        localizer: MessageLocalizer,
        /,
        *,
        timeout: float | None = 180,
    ) -> None:
        super().__init__(timeout=timeout)

        self.add_item(
            discord.ui.Button(label=localizer.format('invite'), url=invite_url)
        )


class AboutView(InviteView):
    def __init__(
        self,
        invite_url: str,
        localizer: MessageLocalizer,
        /,
        *,
        timeout: float | None = 180,
    ) -> None:
        super().__init__(invite_url, localizer, timeout=timeout)

        self.add_item(
            discord.ui.Button(
                label=localizer.format('support-server'),
                url='https://discord.gg/ncZtNu5zgs',
            )
        )

        self.add_item(
            discord.ui.Button(
                label='Github', url='https://github.com/bryanforbes/Erasmus'
            )
        )


class Misc(Cog['Erasmus']):
    localizer: Localizer
    version_map: OrderedDict[str, list[str]]

    def __init__(self, bot: Erasmus, /) -> None:
        super().__init__(bot)

        self.localizer = bot.localizer

    async def refresh(self, _: object = None, /) -> None:
        version_map: OrderedDict[str, list[str]] = OrderedDict()
        current_items: list[str] = []

        with open(Path(__file__).resolve().parent.parent.parent / 'NEWS.md', 'r') as f:
            for line in f.readlines():
                if line.startswith('# Version '):
                    current_items = []
                    version_map[line[10:-1]] = current_items

                if line.startswith('* '):
                    current_items.append(f'• {line[2:-1]}')

        self.version_map = version_map

    async def cog_load(self) -> None:
        await self.refresh()

    @app_commands.command()
    @app_commands.checks.cooldown(rate=2, per=30.0, key=lambda itx: itx.channel_id)
    async def invite(self, itx: discord.Interaction, /) -> None:
        '''Get a link to invite Erasmus to your server'''

        localizer = self.localizer.for_message('about', locale=itx.locale)

        await utils.send(itx, view=InviteView(self.bot.invite_url, localizer))

    @app_commands.command()
    @app_commands.checks.cooldown(rate=2, per=30.0, key=lambda itx: itx.user.id)
    async def about(self, itx: discord.Interaction, /) -> None:
        '''Get info about Erasmus'''

        localizer = self.localizer.for_message('about', locale=itx.locale)
        channel_count = 0
        guild_count = 0

        for guild in self.bot.guilds:
            guild_count += 1

            if guild.unavailable or guild.member_count is None:
                continue

            channels = filter(
                lambda c: isinstance(c, discord.TextChannel), guild.channels
            )
            channel_count += len(list(channels))

        dpy_version = metadata.version('discord.py')
        erasmus_version = metadata.version('erasmus')

        await utils.send(
            itx,
            embeds=[
                Embed(
                    title=localizer.format('title'),
                    fields=[
                        {
                            'name': localizer.format('version'),
                            'value': erasmus_version,
                            'inline': False,
                        },
                        {'name': localizer.format('guilds'), 'value': str(guild_count)},
                        {
                            'name': localizer.format('channels'),
                            'value': str(channel_count),
                        },
                    ],
                    footer={
                        'text': localizer.format(
                            'footer', data={'version': dpy_version}
                        ),
                        'icon_url': 'http://i.imgur.com/5BFecvA.png',
                    },
                    timestamp=discord.utils.utcnow(),
                )
            ],
            view=AboutView(self.bot.invite_url, localizer),
        )

    async def __news_version_autocomplete(
        self, _: discord.Interaction, current: str, /
    ) -> list[app_commands.Choice[str]]:
        versions = self.version_map.keys()
        return [
            app_commands.Choice(name=version, value=version)
            for version in versions
            if current.lower() in version.lower()
        ][:25]

    @app_commands.command()
    @app_commands.checks.cooldown(rate=2, per=30.0, key=lambda itx: itx.channel_id)
    @app_commands.autocomplete(version=__news_version_autocomplete)
    async def news(
        self, itx: discord.Interaction, /, version: str | None = None
    ) -> None:
        '''Display news from the latest release'''

        if version is None or version not in self.version_map:
            version = next(iter(self.version_map))

        localizer = self.localizer.for_message('news', locale=itx.locale)

        await utils.send_embed(
            itx,
            title=localizer.format('news-for-version', data={'version': version}),
            description='\n'.join(self.version_map[version]),
            color=discord.Color.blue(),
        )

    @app_commands.command()
    @app_commands.checks.cooldown(rate=2, per=30.0, key=lambda itx: itx.channel_id)
    async def notice(self, itx: discord.Interaction, /) -> None:
        '''Display text-command deprecation notice'''

        await utils.send_embed(
            itx,
            title='Notice of future changes',
            description=(
                f'{formatting.underline(formatting.bold("Users"))}\n'
                'Beginning <t:1661972400:D>, Erasmus will no longer respond to '
                'text-based commands (`$confess` and others). At that time, Discord '
                'will require all bots to use slash commands. Because of this '
                'new requirement, all text-based commands have been converted into '
                'slash commands. However, Erasmus will still respond to bracket '
                'citations (`[John 1:1]`).\n\n'
                'To see a list of commands available, type `/` in the text input '
                'for a server Erasmus is in and select its icon in the popup.\n\n'
                f'{formatting.underline(formatting.bold("Server Moderators"))}\n'
                'In order to allow your users to use the new slash commands, '
                'you should reauthorize Erasmus in your server by doing the '
                'following (**NOTE:** You **do not** have to remove Erasmus from your '
                'server):\n\n'
                f'- Click [this link]({self.bot.invite_url})\n'
                '- In the popup that opens, select your server in the drop down and '
                'tap "Continue"\n'
                '- In the popup that opens, tap "Authorize"\n\n'
                'To see this message again, run `/notice`.'
            ),
            color=discord.Color.yellow(),
        )


async def setup(bot: Erasmus, /) -> None:
    await bot.add_cog(Misc(bot))

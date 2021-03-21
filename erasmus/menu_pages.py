from __future__ import annotations

import asyncio
from collections.abc import Sequence
from typing import TYPE_CHECKING, Generic, TypeVar, cast

import discord
from botus_receptus import formatting
from discord.ext import commands, menus

T = TypeVar('T')
PS = TypeVar('PS', bound='menus.PageSource[Any]')
TPS = TypeVar('TPS', bound='TotalPageSource[Any]')

if TYPE_CHECKING:
    from typing import Any  # noqa

    class _PageSource(menus.PageSource[T]):
        ...

    class _ListPageSource(menus.ListPageSource[T]):
        ...

    class _MenuPages(menus.MenuPages[PS]):
        ...


else:

    class _PageSource(menus.PageSource, Generic[T]):
        ...

    class _ListPageSource(menus.ListPageSource, Generic[T]):
        ...

    class _MenuPages(menus.MenuPages, Generic[PS]):
        ...


class TotalPageSource(_PageSource[T]):
    def get_total(self, /) -> int:
        return 0


EPS = TypeVar('EPS', bound='EmbedPageSource[Any]')


class EmbedPageSource(TotalPageSource[T]):
    embed: discord.Embed

    async def prepare(self, /) -> None:
        self.embed = discord.Embed()

    async def format_page(
        self: EPS,
        menu: menus.MenuPages[EPS],
        page: T,
        /,
    ) -> discord.Embed:
        self.embed.clear_fields()
        self.embed.description = discord.Embed.Empty

        await self.set_page_text(page)

        maximum = self.get_max_pages()

        if maximum is not None and maximum > 1:
            text = (
                f'Page {menu.current_page + 1}/{maximum} ({self.get_total()} entries)'
            )
            self.embed.set_footer(text=text)

        return self.embed

    async def set_page_text(self, page: T, /) -> None:
        ...


class TotalListPageSource(_ListPageSource[T], TotalPageSource[Sequence[T]]):
    def get_total(self, /) -> int:
        return len(self.entries)


class MenuPages(_MenuPages[TPS]):
    def __init__(self, source: TPS, zero_results_text: str, /) -> None:
        self.zero_results_text = zero_results_text
        self.help_task: asyncio.Task[None] | None = None

        super().__init__(source, timeout=120, check_embeds=True)

    async def start(
        self,
        ctx: commands.Context,
        /,
        *,
        channel: discord.abc.Messageable | None = None,
        wait: bool = False,
    ) -> None:
        await self.source._prepare_once()

        if self.source.get_total() > 0:
            await super().start(ctx, channel=channel, wait=wait)
        else:
            await ctx.send(embed=discord.Embed(description='I found 0 results'))

    @menus.button('\N{INFORMATION SOURCE}', position=menus.Last(3))
    async def show_help(self, payload: discord.RawReactionActionEvent, /) -> None:
        '''shows this message'''
        messages = [
            'Welcome to the interactive pager!\n',
            'This interactively allows you to see pages of text by navigating with '
            'reactions. They are as follows:\n',
        ]

        for emoji, button in self.buttons.items():
            messages.append(f'{emoji} - {button.action.__doc__}')

        if not self._can_remove_reactions:
            messages.append(
                '\n'
                + formatting.warning(
                    'Giving me "Manage Messages" permissions will provide a better '
                    'user experience for the interactive pager'
                )
            )

        embed = discord.Embed(description='\n'.join(messages))
        embed.description = '\n'.join(messages)
        embed.set_footer(
            text=f'You were on page {self.current_page + 1} before this message.'
        )

        await self.message.edit(embed=embed)

        async def go_back_to_current_page() -> None:
            try:
                await asyncio.sleep(30.0)
            except asyncio.CancelledError:
                pass
            finally:
                if self._running:
                    self.help_task = None
                    await self.show_current_page()

        self.help_task = self.bot.loop.create_task(go_back_to_current_page())

    @menus.button('\N{INPUT SYMBOL FOR NUMBERS}', position=menus.Last(1.5))
    async def numbered_page(self, payload: discord.RawReactionActionEvent, /) -> None:
        '''lets you type a page number to go to'''
        channel = self.message.channel
        author_id = payload.user_id

        to_delete: list[discord.Message] = []
        to_delete.append(await channel.send('What page do you want to go to?'))

        def message_check(msg: discord.Message, /) -> bool:
            return (
                msg.author.id == author_id
                and channel == msg.channel
                and msg.content.isdigit()
            )

        try:
            message = await self.bot.wait_for(
                'message', check=message_check, timeout=30.0
            )
        except asyncio.TimeoutError:
            to_delete.append(await channel.send('Took too long.'))
            await asyncio.sleep(5)
        else:
            page = int(message.content)
            to_delete.append(message)
            max_pages = self.source.get_max_pages()
            if max_pages is None or page > 0 and page <= max_pages:
                await self.show_page(page - 1)
            else:
                to_delete.append(
                    await channel.send(f'Invalid page given. ({page}/{max_pages})')
                )
                await asyncio.sleep(5)

        try:
            await cast(discord.TextChannel, channel).delete_messages(to_delete)
        except Exception:
            pass

    async def finalize(self, timed_out: bool, /) -> None:
        if self.help_task is not None:
            self.help_task.cancel()
            self.help_task = None

        try:
            if timed_out:
                await self.message.clear_reactions()
            else:
                await self.message.delete()
        except discord.HTTPException:
            pass

    def reaction_check(self, payload: discord.RawReactionActionEvent, /) -> bool:
        process = super().reaction_check(payload)

        if process and self.help_task:
            self.help_task.cancel()
            self.help_task = None
            return False

        return process

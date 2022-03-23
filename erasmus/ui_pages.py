from __future__ import annotations

import asyncio
from abc import abstractmethod
from collections.abc import Sequence
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from typing_extensions import Self

import discord

from .context import Context
from .page_source import BasePages, PageSource

T = TypeVar('T')


class UIPages(discord.ui.View, BasePages[T], Generic[T]):
    check_embeds: bool
    compact: bool
    message: discord.Message | None
    input_lock: asyncio.Lock

    def __init__(
        self,
        source: PageSource[T],
        /,
        *,
        check_embeds: bool = True,
        compact: bool = False,
        timeout: float | None = 180.0,
    ) -> None:
        BasePages[T].__init__(self, source)
        discord.ui.View.__init__(self, timeout=timeout)

        self.source = source
        self.check_embeds = check_embeds
        self.message = None
        self.current_page = 0
        self.compact = compact
        self.input_lock = asyncio.Lock()
        self.clear_items()

    @abstractmethod
    async def is_same_user(self, interaction: discord.Interaction, /) -> bool:
        ...

    @abstractmethod
    def has_embed_permission(self) -> bool:
        ...

    @abstractmethod
    async def send_initial_message(
        self,
        content: str = discord.utils.MISSING,
        *,
        tts: bool = False,
        ephemeral: bool = discord.utils.MISSING,
        embed: discord.Embed = discord.utils.MISSING,
        embeds: Sequence[discord.Embed] = discord.utils.MISSING,
        file: discord.File = discord.utils.MISSING,
        files: Sequence[discord.File] = discord.utils.MISSING,
        stickers: Sequence[discord.GuildSticker | discord.StickerItem] | None = None,
        delete_after: float | None = None,
        nonce: str | int | None = None,
        allowed_mentions: discord.AllowedMentions = discord.utils.MISSING,
        mention_author: bool | None = None,
        view: discord.ui.View = discord.utils.MISSING,
        suppress_embeds: bool = False,
    ) -> discord.Message:
        ...

    def fill_items(self, /) -> None:
        if not self.compact:
            self.numbered_page.row = 1
            self.stop_pages.row = 1

        if self.source.needs_pagination:
            max_pages = self.source.get_max_pages()
            use_last_and_first = max_pages is not None and max_pages >= 2
            if use_last_and_first:
                self.add_item(self.go_to_first_page)
            self.add_item(self.go_to_previous_page)
            if not self.compact:
                self.add_item(self.go_to_current_page)
            self.add_item(self.go_to_next_page)
            if use_last_and_first:
                self.add_item(self.go_to_last_page)
            if not self.compact:
                self.add_item(self.numbered_page)
            self.add_item(self.stop_pages)

    async def show_page(
        self,
        interaction: discord.Interaction,
        page_number: int,
        /,
    ) -> None:
        page = await self.source.get_page(page_number)
        self.current_page = page_number
        kwargs = await self._get_kwargs_from_page(page)
        self._update_labels(page_number)
        if kwargs:
            if interaction.response.is_done():
                if self.message:
                    await self.message.edit(**kwargs, view=self)
            else:
                await interaction.response.edit_message(**kwargs, view=self)

    def _update_labels(self, page_number: int, /) -> None:
        self.go_to_first_page.disabled = page_number == 0
        if self.compact:
            max_pages = self.source.get_max_pages()
            self.go_to_last_page.disabled = (
                max_pages is None or (page_number + 1) >= max_pages
            )
            self.go_to_next_page.disabled = (
                max_pages is not None and (page_number + 1) >= max_pages
            )
            self.go_to_previous_page.disabled = page_number == 0
            return

        self.go_to_current_page.label = str(page_number + 1)
        self.go_to_previous_page.label = str(page_number)
        self.go_to_next_page.label = str(page_number + 2)
        self.go_to_next_page.disabled = False
        self.go_to_previous_page.disabled = False
        self.go_to_first_page.disabled = False

        max_pages = self.source.get_max_pages()
        if max_pages is not None:
            self.go_to_last_page.disabled = (page_number + 1) >= max_pages
            if (page_number + 1) >= max_pages:
                self.go_to_next_page.disabled = True
                self.go_to_next_page.label = '…'
            if page_number == 0:
                self.go_to_previous_page.disabled = True
                self.go_to_previous_page.label = '…'

    async def show_checked_page(
        self,
        interaction: discord.Interaction,
        page_number: int,
        /,
    ) -> None:
        max_pages = self.source.get_max_pages()
        try:
            if max_pages is None:
                # If it doesn't give maximum pages, it cannot be checked
                await self.show_page(interaction, page_number)
            elif max_pages > page_number >= 0:
                await self.show_page(interaction, page_number)
        except IndexError:
            # An error happened that can be handled, so ignore it.
            pass

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if await self.is_same_user(interaction):
            return True

        await interaction.response.send_message(
            'This pagination menu cannot be controlled by you, sorry!', ephemeral=True
        )

        return False

    async def on_timeout(self) -> None:
        if self.message:
            await self.message.edit(view=None)

    async def on_error(
        self,
        error: Exception,
        item: discord.ui.Item[Self],
        interaction: discord.Interaction,
    ) -> None:
        print(error)
        if interaction.response.is_done():
            await interaction.followup.send(
                'An unknown error occurred, sorry', ephemeral=True
            )
        else:
            await interaction.response.send_message(
                'An unknown error occurred, sorry', ephemeral=True
            )

    async def start(self) -> None:
        if self.check_embeds and not self.has_embed_permission():
            await self.send_initial_message(
                'Bot does not have embed links permission in this channel.',
            )
            return

        await self.source._prepare_once()

        if self.source.get_total() <= 0:
            kwargs = await self._get_kwargs_from_page(None)
            await self.send_initial_message(**kwargs, ephemeral=True)
            return

        self.fill_items()

        page = await self.source.get_page(0)
        kwargs = await self._get_kwargs_from_page(page)
        self._update_labels(0)
        self.message = await self.send_initial_message(
            **kwargs, ephemeral=True, view=self
        )

    @discord.ui.button(label='≪', style=discord.ButtonStyle.grey)
    async def go_to_first_page(
        self, button: discord.ui.Button[Self], interaction: discord.Interaction
    ) -> None:
        await self.show_page(interaction, 0)

    @discord.ui.button(label='Back', style=discord.ButtonStyle.blurple)
    async def go_to_previous_page(
        self, button: discord.ui.Button[Self], interaction: discord.Interaction
    ) -> None:
        await self.show_checked_page(interaction, self.current_page - 1)

    @discord.ui.button(label='Current', style=discord.ButtonStyle.grey, disabled=True)
    async def go_to_current_page(
        self, button: discord.ui.Button[Self], interaction: discord.Interaction
    ) -> None:
        ...

    @discord.ui.button(label='Next', style=discord.ButtonStyle.blurple)
    async def go_to_next_page(
        self, button: discord.ui.Button[Self], interaction: discord.Interaction
    ) -> None:
        await self.show_checked_page(interaction, self.current_page + 1)

    @discord.ui.button(label='≫', style=discord.ButtonStyle.grey)
    async def go_to_last_page(
        self, button: discord.ui.Button[Self], interaction: discord.Interaction
    ) -> None:
        max_pages = self.source.get_max_pages()
        assert max_pages is not None
        await self.show_page(interaction, max_pages - 1)

    @discord.ui.button(label='Skip to page...', style=discord.ButtonStyle.grey)
    async def numbered_page(
        self, button: discord.ui.Button[Self], interaction: discord.Interaction
    ) -> None:
        if self.input_lock.locked():
            await interaction.response.send_message(
                'Already waiting for your response...', ephemeral=True
            )
            return

        if self.message is None:
            return

        async with self.input_lock:
            channel_id = interaction.channel_id
            author_id = interaction.user.id

            await interaction.response.send_message(
                'What page do you want to go to?', ephemeral=True
            )

            def message_check(m: discord.Message) -> bool:
                return (
                    m.author.id == author_id
                    and channel_id == m.channel.id
                    and m.content.isdigit()
                )

            try:
                msg = await interaction.client.wait_for(
                    'message', check=message_check, timeout=30.0
                )
            except asyncio.TimeoutError:
                await interaction.followup.send('Took too long.', ephemeral=True)
                await asyncio.sleep(5)
            else:
                page = int(msg.content)
                await msg.delete()
                await self.show_checked_page(interaction, page - 1)

    @discord.ui.button(label='Quit', style=discord.ButtonStyle.red)
    async def stop_pages(
        self, button: discord.ui.Button[Self], interaction: discord.Interaction
    ) -> None:
        if self.message:
            await self.message.edit(view=None)

        self.stop()


class ContextUIPages(UIPages[T]):
    ctx: Context

    def __init__(
        self,
        source: PageSource[T],
        /,
        *,
        ctx: Context,
        check_embeds: bool = True,
        compact: bool = False,
        timeout: float | None = 180.0,
    ) -> None:
        super().__init__(
            source, check_embeds=check_embeds, compact=compact, timeout=timeout
        )
        self.ctx = ctx

    async def is_same_user(self, interaction: discord.Interaction, /) -> bool:
        return interaction.user.id in (
            self.ctx.bot.owner_id,
            self.ctx.author.id,
        )

    def has_embed_permission(self) -> bool:
        return (
            not isinstance(self.ctx.channel, discord.PartialMessageable)
            and isinstance(self.ctx.me, discord.Member)
            and self.ctx.channel.permissions_for(self.ctx.me).embed_links
        )

    async def send_initial_message(
        self,
        content: str = discord.utils.MISSING,
        *,
        tts: bool = False,
        ephemeral: bool = discord.utils.MISSING,
        embed: discord.Embed = discord.utils.MISSING,
        embeds: Sequence[discord.Embed] = discord.utils.MISSING,
        file: discord.File = discord.utils.MISSING,
        files: Sequence[discord.File] = discord.utils.MISSING,
        stickers: Sequence[discord.GuildSticker | discord.StickerItem] | None = None,
        delete_after: float | None = None,
        nonce: str | int | None = None,
        allowed_mentions: discord.AllowedMentions = discord.utils.MISSING,
        mention_author: bool | None = None,
        view: discord.ui.View = discord.utils.MISSING,
        suppress_embeds: bool = False,
    ) -> discord.Message:
        return await self.ctx.send(  # type: ignore
            content,
            tts=tts,
            embed=embed,
            embeds=embeds,
            file=file,
            files=files,
            stickers=stickers,
            delete_after=delete_after,
            nonce=nonce,
            allowed_mentions=allowed_mentions,
            reference=self.ctx.message,
            mention_author=mention_author,
            view=view,
            suppress_embeds=suppress_embeds,
        )


class InteractionUIPages(UIPages[T]):
    interaction: discord.Interaction

    def __init__(
        self,
        source: PageSource[T],
        /,
        *,
        interaction: discord.Interaction,
        check_embeds: bool = True,
        compact: bool = False,
        timeout: float | None = 180.0,
    ) -> None:
        super().__init__(
            source, check_embeds=check_embeds, compact=compact, timeout=timeout
        )
        self.interaction = interaction

    async def is_same_user(self, interaction: discord.Interaction, /) -> bool:
        return interaction.user.id in (
            self.interaction.client.user
            if self.interaction.client.user is not None
            else None,
            self.interaction.user.id,
        )

    def has_embed_permission(self) -> bool:
        return True

    async def send_initial_message(
        self,
        content: str = discord.utils.MISSING,
        *,
        tts: bool = False,
        ephemeral: bool = discord.utils.MISSING,
        embed: discord.Embed = discord.utils.MISSING,
        embeds: Sequence[discord.Embed] = discord.utils.MISSING,
        file: discord.File = discord.utils.MISSING,
        files: Sequence[discord.File] = discord.utils.MISSING,
        stickers: Sequence[discord.GuildSticker | discord.StickerItem] | None = None,
        delete_after: float | None = None,
        nonce: str | int | None = None,
        allowed_mentions: discord.AllowedMentions = discord.utils.MISSING,
        mention_author: bool | None = None,
        view: discord.ui.View = discord.utils.MISSING,
        suppress_embeds: bool = False,
    ) -> discord.Message:
        if self.interaction.response.is_done():
            await self.interaction.followup.send(
                content,
                tts=tts,
                embed=embed,
                embeds=embeds,
                file=file,
                files=files,
                view=view,
                ephemeral=ephemeral,
                allowed_mentions=allowed_mentions,
                suppress_embeds=suppress_embeds,
            )
        else:
            await self.interaction.response.send_message(
                content,
                tts=tts,
                embed=embed,
                embeds=embeds,
                file=file,
                files=files,
                view=view,
                ephemeral=ephemeral,
                allowed_mentions=allowed_mentions,
                suppress_embeds=suppress_embeds,
            )

        return await self.interaction.original_message()

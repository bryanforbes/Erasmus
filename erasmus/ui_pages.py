from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Final, Generic, TypeVar, cast
from typing_extensions import Self

import discord
from botus_receptus import utils
from discord.ext import commands

from .erasmus import Erasmus
from .page_source import BasePages, PageSource

T = TypeVar('T')


_MISSING: Final = discord.utils.MISSING


class PagesModal(discord.ui.Modal, title='Skip to page…'):
    pages: 'UIPages[Any]'

    def __init__(self, pages: 'UIPages[Any]', *, timeout: float | None = None) -> None:
        super().__init__(timeout=timeout)

        self.pages = pages

    page_number: discord.ui.TextInput[Self] = discord.ui.TextInput(
        label='Page', placeholder='Page number here…'
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        assert self.page_number.value is not None

        if not self.page_number.value.isdigit():
            raise ValueError('You must enter a number')

        await self.pages.show_checked_page(interaction, int(self.page_number.value) - 1)

    async def on_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        message = 'An error occurred'

        if isinstance(error, ValueError):
            message = error.args[0]

        await interaction.response.send_message(
            embed=discord.Embed(description=message, color=discord.Color.red()),
            ephemeral=True,
        )


class UIPages(discord.ui.View, BasePages[T], Generic[T]):
    ctx: commands.Context[Erasmus] | discord.Interaction
    check_embeds: bool
    compact: bool
    message: discord.Message | None

    def __init__(
        self,
        ctx: commands.Context[Erasmus] | discord.Interaction,
        source: PageSource[T],
        /,
        *,
        check_embeds: bool = True,
        compact: bool = False,
        timeout: float | None = 180.0,
    ) -> None:
        super().__init__(timeout=timeout)
        BasePages.__init__(self, source)  # type: ignore

        self.ctx = ctx
        self.check_embeds = check_embeds
        self.message = None
        self.compact = compact
        self.clear_items()

    @discord.utils.cached_property
    def allowed_user_ids(self) -> set[int]:
        if isinstance(self.ctx, commands.Context):
            client: Any = self.ctx.bot
            author_id = self.ctx.author.id
        else:
            client = self.ctx.client
            author_id = self.ctx.user.id

        return {
            author_id,
            client.owner_id,
            cast(discord.ClientUser, client.user).id,
        }

    async def is_same_user(self, interaction: discord.Interaction, /) -> bool:
        return interaction.user.id in self.allowed_user_ids

    def has_embed_permission(self) -> bool:
        if isinstance(self.ctx, commands.Context):
            return (
                isinstance(self.ctx.me, discord.Member)
                and self.ctx.channel.permissions_for(
                    self.ctx.me  # type: ignore
                ).embed_links
            )

        return True

    async def send_initial_message(
        self,
        content: str = _MISSING,
        *,
        tts: bool = False,
        ephemeral: bool = _MISSING,
        embed: discord.Embed = _MISSING,
        embeds: Sequence[discord.Embed] = _MISSING,
        file: discord.File = _MISSING,
        files: Sequence[discord.File] = _MISSING,
        delete_after: float = _MISSING,
        nonce: int = _MISSING,
        allowed_mentions: discord.AllowedMentions = _MISSING,
        view: discord.ui.View = _MISSING,
    ) -> discord.Message:
        return await utils.send(  # type: ignore
            self.ctx,
            content=content,
            tts=tts,
            ephemeral=ephemeral,
            embed=embed,
            embeds=embeds,
            file=file,
            files=files,
            view=view,
            allowed_mentions=allowed_mentions,
            nonce=nonce,
            delete_after=delete_after,
        )

    def fill_items(self, /) -> None:
        if not self.compact:
            # self.numbered_page.row = 1
            self.stop_pages.row = 1

        if self.source.needs_pagination:
            max_pages = self.source.get_max_pages()
            use_last_and_first = max_pages is not None and max_pages >= 2
            if use_last_and_first:
                self.add_item(self.go_to_first_page)
            self.add_item(self.go_to_previous_page)
            if not self.compact:
                self.add_item(self.skip_to_page)
            self.add_item(self.go_to_next_page)
            if use_last_and_first:
                self.add_item(self.go_to_last_page)
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

        self.skip_to_page.label = str(page_number + 1)
        self.go_to_next_page.disabled = False
        self.go_to_previous_page.disabled = False
        self.go_to_first_page.disabled = False

        max_pages = self.source.get_max_pages()
        if max_pages is not None:
            self.go_to_last_page.disabled = (page_number + 1) >= max_pages
            if (page_number + 1) >= max_pages:
                self.go_to_next_page.disabled = True
            if page_number == 0:
                self.go_to_previous_page.disabled = True

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
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item[Self],
    ) -> None:
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
        self, interaction: discord.Interaction, button: discord.ui.Button[Self]
    ) -> None:
        await self.show_page(interaction, 0)

    @discord.ui.button(label='<', style=discord.ButtonStyle.blurple)
    async def go_to_previous_page(
        self, interaction: discord.Interaction, button: discord.ui.Button[Self]
    ) -> None:
        await self.show_checked_page(interaction, self.current_page - 1)

    @discord.ui.button(label='Current', style=discord.ButtonStyle.blurple)
    async def skip_to_page(
        self, interaction: discord.Interaction, button: discord.ui.Button[Self]
    ) -> None:
        await interaction.response.send_modal(PagesModal(self))

    @discord.ui.button(label='>', style=discord.ButtonStyle.blurple)
    async def go_to_next_page(
        self, interaction: discord.Interaction, button: discord.ui.Button[Self]
    ) -> None:
        await self.show_checked_page(interaction, self.current_page + 1)

    @discord.ui.button(label='≫', style=discord.ButtonStyle.grey)
    async def go_to_last_page(
        self, interaction: discord.Interaction, button: discord.ui.Button[Self]
    ) -> None:
        max_pages = self.source.get_max_pages()
        assert max_pages is not None
        await self.show_page(interaction, max_pages - 1)

    @discord.ui.button(label='Stop', style=discord.ButtonStyle.red)
    async def stop_pages(
        self, interaction: discord.Interaction, button: discord.ui.Button[Self]
    ) -> None:
        if self.message:
            await self.message.edit(view=None)

        self.stop()

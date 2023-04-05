from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Final, Generic, TypeVar, cast
from typing_extensions import Self, override

import discord
from botus_receptus import utils

from .page_source import BasePages, PageSource

if TYPE_CHECKING:
    from collections.abc import Sequence

    from botus_receptus.types import Coroutine

    from .erasmus import Erasmus
    from .l10n import MessageLocalizer

T = TypeVar('T')


_MISSING: Final = discord.utils.MISSING


class PagesModal(discord.ui.Modal, Generic[T], title='Skip to page…'):
    pages: UIPages[T]

    def __init__(self, pages: UIPages[T], *, timeout: float | None = None) -> None:
        super().__init__(timeout=timeout)

        self.pages = pages

        self.title = self.pages.localizer.format('modal-title')
        self.page_number.label = self.pages.localizer.format('modal-input-label')
        self.page_number.placeholder = self.pages.localizer.format(
            'modal-input-placeholder'
        )

    page_number: discord.ui.TextInput[Self] = discord.ui.TextInput(
        label='Page', placeholder='Page number here…'
    )

    @override
    async def on_submit(self, itx: discord.Interaction, /) -> None:
        assert self.page_number.value is not None

        if not self.page_number.value.isdigit():
            raise ValueError(self.pages.localizer.format('modal-not-a-number-error'))

        await self.pages.show_checked_page(itx, int(self.page_number.value) - 1)

    @override
    async def on_error(self, itx: discord.Interaction, error: Exception, /) -> None:
        if isinstance(error, ValueError):
            message = error.args[0]
        else:
            message = self.pages.localizer.format('modal-generic-error')

        await itx.response.send_message(
            embed=discord.Embed(description=message, color=discord.Color.red()),
            ephemeral=True,
        )


class UIPages(discord.ui.View, BasePages[T], Generic[T]):
    itx: discord.Interaction
    check_embeds: bool
    compact: bool
    message: discord.Message | None
    localizer: MessageLocalizer
    allowed_mentions: discord.AllowedMentions

    def __init__(
        self,
        itx: discord.Interaction,
        source: PageSource[T],
        /,
        *,
        localizer: MessageLocalizer,
        check_embeds: bool = True,
        compact: bool = False,
        timeout: float | None = 180.0,
        allowed_mentions: discord.AllowedMentions = _MISSING,
    ) -> None:
        super().__init__(timeout=timeout)
        BasePages.__init__(self, source)  # type: ignore

        self.itx = itx
        self.check_embeds = check_embeds
        self.message = None
        self.compact = compact
        self.localizer = localizer
        self.allowed_mentions = allowed_mentions
        self.clear_items()

    @discord.utils.cached_property
    def allowed_user_ids(self) -> set[int]:
        client = cast('Erasmus', self.itx.client)
        author_id = self.itx.user.id

        return {
            author_id,
            cast('int', client.owner_id),
            client.user.id,
        }

    async def is_same_user(self, itx: discord.Interaction, /) -> bool:
        return itx.user.id in self.allowed_user_ids

    def has_embed_permission(self) -> bool:
        return True

    def send_initial_message(
        self,
        content: str = _MISSING,
        *,
        tts: bool = False,
        ephemeral: bool = _MISSING,
        embeds: Sequence[discord.Embed] = _MISSING,
        files: Sequence[discord.File] = _MISSING,
        delete_after: float = _MISSING,
        nonce: int = _MISSING,
        view: discord.ui.View = _MISSING,
    ) -> Coroutine[discord.Message]:
        return utils.send(
            self.itx,
            content=content,
            tts=tts,
            ephemeral=ephemeral,
            embeds=embeds,
            files=files,
            view=view,
            allowed_mentions=self.allowed_mentions,
            nonce=nonce,
            delete_after=delete_after,
        )

    def fill_items(self, /) -> None:
        if not self.compact:
            # self.numbered_page.row = 1
            self.stop_pages.row = 1

        self.stop_pages.label = self.localizer.format('stop-button')

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

    async def show_page(self, itx: discord.Interaction, page_number: int, /) -> None:
        page = await self.source.get_page(page_number)
        self.current_page = page_number
        kwargs = await self._get_kwargs_from_page(page)
        self._update_labels(page_number)
        if kwargs:
            if itx.response.is_done():
                if self.message:
                    await self.message.edit(
                        **kwargs, view=self, allowed_mentions=self.allowed_mentions
                    )
            else:
                await itx.response.edit_message(
                    **kwargs, view=self, allowed_mentions=self.allowed_mentions
                )

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
        self, itx: discord.Interaction, page_number: int, /
    ) -> None:
        max_pages = self.source.get_max_pages()
        with contextlib.suppress(IndexError):
            if max_pages is None or max_pages > page_number >= 0:
                # If it doesn't give maximum pages, it cannot be checked
                await self.show_page(itx, page_number)

    @override
    async def interaction_check(self, itx: discord.Interaction, /) -> bool:
        if await self.is_same_user(itx):
            return True

        await itx.response.send_message(
            self.localizer.format('cannot-be-controlled-error'),
            ephemeral=True,
        )

        return False

    @override
    async def on_timeout(self) -> None:
        if self.message:
            await self.message.edit(view=None)

    @override
    async def on_error(
        self, itx: discord.Interaction, error: Exception, item: discord.ui.Item[Self], /
    ) -> None:
        await utils.send(
            itx,
            content=self.localizer.format('unknown-error'),
            ephemeral=True,
        )

    async def start(self) -> None:
        if self.check_embeds and not self.has_embed_permission():
            await self.send_initial_message(self.localizer.format('embed-links-error'))
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
        self, itx: discord.Interaction, button: discord.ui.Button[Self], /
    ) -> None:
        await self.show_page(itx, 0)

    @discord.ui.button(label='<', style=discord.ButtonStyle.blurple)
    async def go_to_previous_page(
        self, itx: discord.Interaction, button: discord.ui.Button[Self], /
    ) -> None:
        await self.show_checked_page(itx, self.current_page - 1)

    @discord.ui.button(label='Current', style=discord.ButtonStyle.blurple)
    async def skip_to_page(
        self, itx: discord.Interaction, button: discord.ui.Button[Self], /
    ) -> None:
        await itx.response.send_modal(PagesModal(self))

    @discord.ui.button(label='>', style=discord.ButtonStyle.blurple)
    async def go_to_next_page(
        self, itx: discord.Interaction, button: discord.ui.Button[Self], /
    ) -> None:
        await self.show_checked_page(itx, self.current_page + 1)

    @discord.ui.button(label='≫', style=discord.ButtonStyle.grey)
    async def go_to_last_page(
        self, itx: discord.Interaction, button: discord.ui.Button[Self], /
    ) -> None:
        max_pages = self.source.get_max_pages()
        assert max_pages is not None
        await self.show_page(itx, max_pages - 1)

    @discord.ui.button(label='Stop', style=discord.ButtonStyle.red)
    async def stop_pages(
        self, itx: discord.Interaction, button: discord.ui.Button[Self], /
    ) -> None:
        if self.message:
            await self.message.edit(view=None)

        self.stop()

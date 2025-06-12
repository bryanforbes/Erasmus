from __future__ import annotations

from typing import TYPE_CHECKING, override

from ...data import Passage
from ...page_source import AsyncCallback, AsyncPageSource, FieldPageSource, Pages

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from ...l10n import MessageLocalizer
    from ...types import Bible


class SearchPageSource(FieldPageSource['Sequence[Passage]'], AsyncPageSource[Passage]):
    bible: Bible
    localizer: MessageLocalizer

    def __init__(
        self,
        callback: AsyncCallback[Passage],
        /,
        *,
        per_page: int,
        bible: Bible,
        localizer: MessageLocalizer,
    ) -> None:
        super().__init__(callback, per_page=per_page)

        self.bible = bible
        self.localizer = localizer

    @override
    def get_field_values(
        self, entries: Sequence[Passage], /
    ) -> Iterable[tuple[str, str]]:
        for entry in entries:
            yield (
                str(entry.range),
                (
                    entry.text
                    if len(entry.text) < 1024
                    else f'{entry.text[:1023]}\u2026'
                ),
            )

    @override
    def format_footer_text(
        self, pages: Pages[Sequence[Passage]], max_pages: int
    ) -> str:
        return self.localizer.format(
            'footer',
            data={
                'current_page': pages.current_page + 1,
                'max_pages': max_pages,
                'total': self.get_total(),
            },
        )

    @override
    async def set_page_text(self, page: Sequence[Passage] | None, /) -> None:
        self.embed.title = self.localizer.format(
            'title', data={'bible_name': self.bible.name}
        )

        if page is None:
            self.embed.description = self.localizer.format('no-results')
            return

        await super().set_page_text(page)

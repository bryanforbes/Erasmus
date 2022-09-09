from __future__ import annotations

from itertools import pairwise
from typing import TYPE_CHECKING, Final, NamedTuple, cast

from attrs import define
from botus_receptus import re, utils
from botus_receptus.cog import GroupCog
from botus_receptus.formatting import EmbedPaginator, bold, escape, underline
from discord import app_commands

from ..db import (
    Confession as ConfessionRecord,
    ConfessionType,
    NumberingType,
    Section,
    Session,
)
from ..exceptions import InvalidConfessionError, NoSectionError
from ..format import alpha_to_int, int_to_alpha, int_to_roman, roman_to_int
from ..page_source import EmbedPageSource, ListPageSource
from ..ui_pages import UIPages
from ..utils import AutoCompleter

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from re import Match
    from typing_extensions import Self

    import discord
    from sqlalchemy.ext.asyncio import AsyncSession

    from ..erasmus import Erasmus
    from ..l10n import Localizer, MessageLocalizer

_roman_re: Final = re.group(
    re.between(0, 4, 'M'),
    re.either('CM', 'CD', re.group(re.optional('D'), re.between(0, 3, 'C'))),
    re.either('XC', 'XL', re.group(re.optional('L'), re.between(0, 3, 'X'))),
    re.either('IX', 'IV', re.group(re.optional('V'), re.between(0, 3, 'I'))),
)

_number_formatters: Final[dict[NumberingType, Callable[[int], str]]] = {
    NumberingType.ARABIC: lambda n: str(n),
    NumberingType.ROMAN: int_to_roman,
    NumberingType.ALPHA: int_to_alpha,
}


_reference_re: Final = re.compile(
    re.START,
    re.either(
        re.named_group('section_arabic')(re.one_or_more(re.DIGITS)),
        re.named_group('section_roman')(_roman_re),
        re.named_group('section_alpha')(re.ALPHA),
    ),
    re.optional(
        re.DOT,
        re.either(
            re.named_group('subsection_arabic')(re.one_or_more(re.DIGITS)),
            re.named_group('subsection_roman')(_roman_re),
            re.named_group('subsection_alpha')(re.ALPHA),
        ),
    ),
    re.END,
    flags=re.IGNORECASE,
)

_break_re: Final = re.compile(r'[.\s;,]+')


def _ellipsize(string: str, /, *, max_length: int) -> tuple[str, str]:
    if len(string) <= max_length:
        return string, string

    max_length = max_length - 1
    result: str | None = None

    for previous, current in pairwise(_break_re.finditer(string)):
        if current.start() >= max_length:
            result = string[: previous.start()]
            break

    if result is None:
        result = string[:max_length].strip()

    return result, f'{result}…'


def _format_section_number(confession: ConfessionRecord, section: Section, /) -> str:
    format_number = _number_formatters[confession.numbering]

    result = format_number(section.number)

    if section.subsection_number is not None:
        format_subsection_number = _number_formatters[confession.subsection_numbering]
        result += f'.{format_subsection_number(section.subsection_number)}'

    return result


async def _get_output(
    session: AsyncSession, confession: ConfessionRecord, match: Match[str], /
) -> tuple[str | None, str]:
    if match['section_arabic']:
        section_number = int(match['section_arabic'])
    elif match['section_roman']:
        section_number = roman_to_int(match['section_roman'])
    else:
        section_number = alpha_to_int(match['section_alpha'])

    if match['subsection_arabic']:
        subsection_number = int(match['subsection_arabic'])
    elif match['subsection_roman']:
        subsection_number = roman_to_int(match['subsection_roman'])
    elif match['subsection_alpha']:
        subsection_number = alpha_to_int(match['subsection_alpha'])
    else:
        subsection_number = None

    section = await confession.get_section(session, section_number, subsection_number)
    formatted_section_number = _format_section_number(confession, section)

    if section.title is not None:
        return f'{formatted_section_number}. {section.title}', section.text
    else:
        return None, f'{bold(formatted_section_number)}. {section.text}'


class ConfessionSearchSource(
    EmbedPageSource['Sequence[Section]'], ListPageSource[Section]
):
    confession: ConfessionRecord
    localizer: MessageLocalizer

    def __init__(
        self,
        entries: list[Section],
        /,
        *,
        per_page: int,
        confession: ConfessionRecord,
        localizer: MessageLocalizer,
    ) -> None:
        super().__init__(entries, per_page=per_page)

        self.confession = confession
        self.localizer = localizer

    async def set_page_text(self, entries: Sequence[Section] | None, /) -> None:
        if entries is None:
            self.embed.description = self.localizer.format('no-results')
            return

        lines: list[str] = []

        for entry in entries:
            section_number = _format_section_number(self.confession, entry)
            lines.append(f'**{section_number}**. {entry.title}')

        self.embed.description = '\n'.join(lines)


class _SectionInfo(NamedTuple):
    section: str
    text: str
    text_lower: str
    choice_name: str
    choice_value: str


@define
class _ConfessionOption:
    command: str
    command_lower: str
    name: str
    name_lower: str
    type: ConfessionType
    section_info: list[_SectionInfo]

    @property
    def key(self) -> str:
        return self.command

    def matches(self, text: str, /) -> bool:
        return text in self.name_lower or text in self.command_lower

    def choice(self) -> app_commands.Choice[str]:
        return app_commands.Choice(name=self.name, value=self.command)

    @classmethod
    def create(cls, confession: ConfessionRecord, /) -> Self:
        section_info: list[_SectionInfo] = []

        for section in confession.sections:
            section_str = _format_section_number(confession, section)
            section_value = f'{section.number}'

            if section.subsection_number is not None:
                section_value += f'.{section.subsection_number}'

            text, choice_name = _ellipsize(
                f'{section_str}. {section.title or section.text}', max_length=100
            )

            section_info.append(
                _SectionInfo(
                    section=section_str,
                    text=text,
                    text_lower=text.lower(),
                    choice_name=choice_name,
                    choice_value=section_value,
                )
            )

        return cls(
            name=confession.name,
            name_lower=confession.name.lower(),
            command=confession.command,
            command_lower=confession.command.lower(),
            type=confession.type,
            section_info=section_info,
        )


@define(eq=False)
class SectionAutoCompleter(app_commands.Transformer):
    confession_lookup: AutoCompleter[_ConfessionOption]

    async def transform(self, itx: discord.Interaction, value: str, /) -> str:
        return value

    async def autocomplete(  # pyright: ignore [reportIncompatibleMethodOverride]
        self, itx: discord.Interaction, value: str, /
    ) -> list[app_commands.Choice[str]]:
        value = value.lower().strip()

        if (
            itx.data is None
            or (options := itx.data.get('options')) is None
            or len(options) != 1
            or (group_options := options[0].get('options')) is None
            or len(group_options) == 0
            or group_options[0].get('name') != 'source'
            or (source := group_options[0].get('value')) is None  # type: ignore
            or (item := self.confession_lookup.get(source)) is None  # type: ignore
        ):
            return []

        return [
            app_commands.Choice(
                name=section_info.choice_name, value=section_info.choice_value
            )
            for section_info in item.section_info
            if not value
            or value in section_info.text_lower
            or value in section_info.section
        ][:25]


_confession_lookup: AutoCompleter[_ConfessionOption] = AutoCompleter()
_section_lookup = SectionAutoCompleter(_confession_lookup)


class Confession(
    GroupCog['Erasmus'],
    group_name='confess',
    group_description='Confessions',
):
    localizer: Localizer

    def __init__(self, bot: Erasmus, /) -> None:
        self.localizer = bot.localizer

        super().__init__(bot)

    async def refresh(self, session: AsyncSession, /) -> None:
        _confession_lookup.clear()
        _confession_lookup.update(
            [
                _ConfessionOption.create(confession)
                async for confession in ConfessionRecord.get_all(
                    session, order_by_name=True, load_sections=True
                )
            ]
        )

    async def cog_load(self) -> None:
        async with Session() as session:
            await self.refresh(session)

    async def cog_unload(self) -> None:
        _confession_lookup.clear()

    async def cog_app_command_error(  # pyright: ignore [reportIncompatibleMethodOverride]  # noqa: B950
        self, itx: discord.Interaction, error: Exception, /
    ) -> None:
        if (
            isinstance(
                error,
                (
                    app_commands.CommandInvokeError,
                    app_commands.TransformerError,
                ),
            )
            and error.__cause__ is not None
        ):
            error = cast('Exception', error.__cause__)

        match error:
            case InvalidConfessionError():
                message_id = 'invalid-confession'
                data = {'confession': error.confession}
            case NoSectionError():
                message_id = 'no-section'
                data = {
                    'confession': error.confession,
                    'section_type': error.section_type,
                    'section': error.section,
                }
            case _:
                return

        await utils.send_embed_error(
            itx,
            description=escape(
                self.localizer.format(message_id, data=data, locale=itx.locale),
                mass_mentions=True,
            ),
        )

    @app_commands.command()
    @app_commands.checks.cooldown(
        rate=2, per=30.0, key=lambda i: (i.guild_id, i.user.id)
    )
    @app_commands.describe(
        source='The confession or catechism to search in', terms='Terms to search for'
    )
    async def search(
        self,
        itx: discord.Interaction,
        /,
        source: app_commands.Transform[str, _confession_lookup],
        terms: str,
    ) -> None:
        '''Search for terms in a confession or catechism'''

        async with Session() as session:
            confession = await ConfessionRecord.get_by_command(session, source)
            results = await confession.search(session, terms.split(' '))

        localizer = self.localizer.for_message('confess__search', itx.locale)
        search_source = ConfessionSearchSource(
            results,
            per_page=20,
            confession=confession,
            localizer=localizer,
        )
        pages = UIPages(itx, search_source, localizer=localizer)
        await pages.start()

    @app_commands.command()
    @app_commands.checks.cooldown(
        rate=8, per=60.0, key=lambda i: (i.guild_id, i.user.id)
    )
    @app_commands.describe(
        source='The confession or catechism to cite', section='The section to cite'
    )
    async def cite(
        self,
        itx: discord.Interaction,
        /,
        source: app_commands.Transform[str, _confession_lookup],
        section: app_commands.Transform[str, _section_lookup],
    ) -> None:
        '''Cite a section from a confession or catechism'''

        async with Session() as session:
            confession = await ConfessionRecord.get_by_command(session, source)

            if (match := _reference_re.match(section)) is None:
                raise NoSectionError(confession.name, section, confession.type)

            section_title, output = await _get_output(session, confession, match)

        paginator = EmbedPaginator()

        title: str | None = underline(bold(confession.name))

        if section_title:
            paginator.add_line(bold(section_title))

        if output:
            paginator.add_line(output)

        for page in paginator:
            await utils.send_embed(itx, description=page, title=title)
            title = None


async def setup(bot: Erasmus, /) -> None:
    await bot.add_cog(Confession(bot))

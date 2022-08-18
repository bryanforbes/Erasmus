from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final, NamedTuple, TypeAlias, cast

import discord
from attrs import define, field
from botus_receptus import Cog, re, utils
from botus_receptus.cog import GroupCog
from botus_receptus.formatting import (
    EmbedPaginator,
    bold,
    ellipsize,
    escape,
    pluralizer,
    underline,
)
from discord import app_commands
from discord.ext import commands

from ..db import (
    Article,
    Confession as ConfessionRecord,
    ConfessionTypeEnum,
    NumberingTypeEnum,
    Paragraph,
    Question,
    Session,
)
from ..exceptions import InvalidConfessionError, NoSectionError, NoSectionsError
from ..format import int_to_roman, roman_to_int
from ..page_source import EmbedPageSource, ListPageSource
from ..ui_pages import UIPages
from ..utils import AutoCompleter

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Awaitable, Callable, Sequence
    from re import Match
    from typing_extensions import Self

    from sqlalchemy.ext.asyncio import AsyncSession

    from ..erasmus import Erasmus
    from ..l10n import Localizer, MessageLocalizer

_roman_re: Final = re.group(
    re.between(0, 4, 'M'),
    re.either('CM', 'CD', re.group(re.optional('D'), re.between(0, 3, 'C'))),
    re.either('XC', 'XL', re.group(re.optional('L'), re.between(0, 3, 'X'))),
    re.either('IX', 'IV', re.group(re.optional('V'), re.between(0, 3, 'I'))),
)

_reference_res: Final = {
    ConfessionTypeEnum.CHAPTERS: re.compile(
        re.START,
        re.either(
            re.group(
                re.named_group('chapter')(re.one_or_more(re.DIGITS)),
                re.DOT,
                re.named_group('paragraph')(re.one_or_more(re.DIGITS)),
            ),
            re.group(
                re.named_group('chapter_roman')(_roman_re),
                re.DOT,
                re.named_group('paragraph_roman')(_roman_re),
            ),
        ),
        re.END,
    ),
    ConfessionTypeEnum.QA: re.compile(
        re.START,
        re.optional(re.named_group('qa')('[qaQA]')),
        re.either(
            re.named_group('number')(re.one_or_more(re.DIGITS)),
            re.named_group('number_roman')(_roman_re),
        ),
        re.END,
    ),
    ConfessionTypeEnum.ARTICLES: re.compile(
        re.START,
        re.either(
            re.named_group('article')(re.one_or_more(re.DIGITS)),
            re.named_group('article_roman')(_roman_re),
        ),
        re.END,
    ),
}

_pluralizers: Final = {
    ConfessionTypeEnum.CHAPTERS: pluralizer('paragraph'),
    ConfessionTypeEnum.ARTICLES: pluralizer('article'),
    ConfessionTypeEnum.QA: pluralizer('question'),
}

_number_formatters: Final[dict[NumberingTypeEnum, Callable[[int], str]]] = {
    NumberingTypeEnum.ARABIC: lambda n: str(n),
    NumberingTypeEnum.ROMAN: int_to_roman,
}


async def _get_chapters_output(
    session: AsyncSession,
    confession: ConfessionRecord,
    match: Match[str],
    /,
) -> tuple[str | None, str]:
    format_number = _number_formatters[confession.numbering]

    if match['chapter_roman']:
        chapter_num = roman_to_int(match['chapter_roman'])
        paragraph_num = roman_to_int(match['paragraph_roman'])
    else:
        chapter_num = int(match['chapter'])
        paragraph_num = int(match['paragraph'])

    paragraph = await confession.get_paragraph(session, chapter_num, paragraph_num)

    paragraph_number = format_number(paragraph.paragraph_number)
    chapter_number = format_number(paragraph.chapter.chapter_number)

    return (
        f'{chapter_number}.{paragraph_number} {paragraph.chapter.chapter_title}',
        paragraph.text,
    )


async def _get_articles_output(
    session: AsyncSession,
    confession: ConfessionRecord,
    match: Match[str],
    /,
) -> tuple[str | None, str]:
    format_number = _number_formatters[confession.numbering]

    if match['article_roman']:
        article_number = roman_to_int(match['article_roman'])
    else:
        article_number = int(match['article'])

    article = await confession.get_article(session, article_number)

    return f'{format_number(article_number)}. {article.title}', article.text


async def _get_qa_output(
    session: AsyncSession,
    confession: ConfessionRecord,
    match: Match[str],
    /,
) -> tuple[str | None, str]:
    format_number = _number_formatters[confession.numbering]

    q_or_a = match['qa']
    if match['number_roman']:
        question_number = roman_to_int(match['number_roman'])
    else:
        question_number = int(match['number'])

    question = await confession.get_question(session, question_number)

    question_number_str = format_number(question_number)

    section_title: str | None = None

    if q_or_a is None:
        section_title = bold(f'{question_number_str}. {question.question_text}')
        output = question.answer_text
    elif q_or_a.lower() == 'q':
        output = f'**Q{question_number_str}**. {question.question_text}'
    else:
        output = f'**A{question_number_str}**: {question.answer_text}'

    return section_title, output


_OUTPUT_GETTER: TypeAlias = '''Callable[
    [
        AsyncSession,
        ConfessionRecord,
        Match[str],
    ],
    Awaitable[tuple[str | None, str]],
]'''

_output_getters: Final[dict[ConfessionTypeEnum, _OUTPUT_GETTER]] = {
    ConfessionTypeEnum.CHAPTERS: _get_chapters_output,
    ConfessionTypeEnum.ARTICLES: _get_articles_output,
    ConfessionTypeEnum.QA: _get_qa_output,
}


_confess_help: Final = '''
Arguments:
----------
    [confession] - A confession to query. Can be found by invoking {prefix}confess
                   with no arguments.

    [args...] - Arguments to pass to query or look up in the confession.

Examples:
---------
    List all confessions/catechisms:
        {prefix}confess

    List the chapters of a confession:
        {prefix}confess 1689

    Show the number of questions in a catechism:
        {prefix}confess hc

    Search for terms in a confession/catechism:
        {prefix}confess 1689 faith hope

    Look up the paragraph of a confession:
        {prefix}confess 1689 2.2

    Look up a question, answer, or both in a catechism:
        {prefix}confess hc q3
        {prefix}confess hc a3
        {prefix}confess hc 3
'''


ConfessionSearchResult: TypeAlias = Paragraph | Article | Question


class ConfessionSearchSource(
    EmbedPageSource['Sequence[ConfessionSearchResult]'],
    ListPageSource[ConfessionSearchResult],
):
    entry_text_string: str
    localizer: MessageLocalizer

    def __init__(
        self,
        entries: list[ConfessionSearchResult],
        /,
        *,
        per_page: int,
        type: ConfessionTypeEnum,
        localizer: MessageLocalizer,
    ) -> None:
        super().__init__(entries, per_page=per_page)

        self.localizer = localizer

        if type == ConfessionTypeEnum.CHAPTERS:
            self.entry_text_string = (
                '**{entry.chapter_number}.{entry.paragraph_number}**. '
                '{entry.chapter.chapter_title}'
            )
        elif type == ConfessionTypeEnum.ARTICLES:
            self.entry_text_string = '**{entry.article_number}**. {entry.title}'
        elif type == ConfessionTypeEnum.QA:
            self.entry_text_string = (
                '**{entry.question_number}**. {entry.question_text}'
            )

    async def set_page_text(
        self,
        entries: Sequence[ConfessionSearchResult] | None,
        /,
    ) -> None:
        if entries is None:
            self.embed.description = self.localizer.format('no-results')
            return

        lines: list[str] = []

        for entry in entries:
            lines.append(self.entry_text_string.format(entry=entry))

        self.embed.description = '\n'.join(lines)


class ConfessionBase(Cog['Erasmus']):
    localizer: Localizer

    def __init__(self, bot: Erasmus, /) -> None:
        self.localizer = bot.localizer

        super().__init__(bot)

    async def cog_command_error(
        self,
        ctx: commands.Context[Any] | discord.Interaction,
        error: Exception,
    ) -> None:
        if (
            isinstance(
                error,
                (
                    commands.CommandInvokeError,
                    commands.BadArgument,
                    commands.ConversionError,
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
            case NoSectionsError():
                message_id = 'no-sections'
                data = {
                    'confession': error.confession,
                    'section_type': error.section_type,
                }
            case _:
                return

        await utils.send_embed_error(
            ctx,
            description=escape(
                self.localizer.format(
                    message_id,
                    data=data,
                    locale=ctx.locale
                    if isinstance(ctx, discord.Interaction)
                    else (
                        ctx.interaction.locale if ctx.interaction is not None else None
                    ),
                ),
                mass_mentions=True,
            ),
        )

    cog_app_command_error = cog_command_error  # type: ignore

    async def _show_citation(
        self,
        ctx: commands.Context[Any] | discord.Interaction,
        confession: ConfessionRecord,
        match: Match[str],
        /,
    ) -> None:
        paginator = EmbedPaginator()
        get_output = _output_getters[confession.type]

        async with Session() as session:
            section_title, output = await get_output(session, confession, match)

        title: str | None = underline(bold(confession.name))

        if section_title:
            paginator.add_line(bold(section_title))

        if output:
            paginator.add_line(output)

        for page in paginator:
            await utils.send_embed(ctx, description=page, title=title)
            title = None


class Confession(ConfessionBase):
    @commands.command(brief='Query confessions and catechisms', help=_confess_help)
    @commands.cooldown(rate=10, per=30.0, type=commands.BucketType.user)
    async def confess(
        self,
        ctx: commands.Context[Erasmus],
        confession: str | None = None,
        /,
        *args: str,
    ) -> None:
        if confession is None:
            await self.list(ctx)
            return

        async with Session() as session:
            row = await ConfessionRecord.get_by_command(session, confession)

        if len(args) == 0:
            await self.list_contents(ctx, row)
            return

        if not (match := _reference_res[row.type].match(args[0])):
            await self.search(ctx, row, *args)
            return

        await self._show_citation(ctx, row, match)

    async def list(self, ctx: commands.Context[Erasmus], /) -> None:
        paginator = EmbedPaginator()
        paginator.add_line('I support the following confessions:', empty=True)

        async with Session() as session:
            async for conf in ConfessionRecord.get_all(session):
                paginator.add_line(f'  `{conf.command}`: {conf.name}')

        for page in paginator:
            await utils.send_embed(ctx, description=page)

    async def list_contents(
        self,
        ctx: commands.Context[Erasmus],
        confession: ConfessionRecord,
        /,
    ) -> None:
        if (
            confession.type == ConfessionTypeEnum.CHAPTERS
            or confession.type == ConfessionTypeEnum.ARTICLES
        ):
            await self.list_sections(ctx, confession)
        elif confession.type == ConfessionTypeEnum.QA:
            await self.list_questions(ctx, confession)

    async def list_sections(
        self,
        ctx: commands.Context[Erasmus],
        confession: ConfessionRecord,
        /,
    ) -> None:
        paginator = EmbedPaginator()
        getter: Callable[[AsyncSession], AsyncIterator[Any]] | None = None
        number_key: str | None = None
        title_key: str | None = None

        if confession.type == ConfessionTypeEnum.CHAPTERS:
            getter = confession.get_chapters
            number_key = 'chapter_number'
            title_key = 'chapter_title'
        else:  # ConfessionTypeEnum.ARTICLES
            getter = confession.get_articles
            number_key = 'article_number'
            title_key = 'title'

        format_number = _number_formatters[confession.numbering]

        async with Session() as session:
            async for record in getter(session):
                paginator.add_line(
                    '**{number}**. {title}'.format(
                        number=format_number(getattr(record, number_key)),
                        title=getattr(record, title_key),
                    )
                )

        for index, page in enumerate(paginator):
            await utils.send_embed(
                ctx,
                description=page,
                title=(underline(bold(confession.name)) if index == 0 else None),
            )

    async def list_questions(
        self,
        ctx: commands.Context[Erasmus],
        confession: ConfessionRecord,
        /,
    ) -> None:
        async with Session() as session:
            count = await confession.get_question_count(session)

        question_str = _pluralizers[ConfessionTypeEnum.QA](count)

        await utils.send_embed(
            ctx, description=f'`{confession.name}` has {question_str}'
        )

    async def search(
        self,
        ctx: commands.Context[Erasmus],
        confession: ConfessionRecord,
        /,
        *terms: str,
    ) -> None:
        if confession.type == ConfessionTypeEnum.CHAPTERS:
            search_func: Callable[
                [AsyncSession, Sequence[str]], AsyncIterator[ConfessionSearchResult]
            ] = confession.search_paragraphs
        elif confession.type == ConfessionTypeEnum.ARTICLES:
            search_func = confession.search_articles
        else:  # ConfessionTypeEnum.QA
            search_func = confession.search_questions

        async with Session() as session:
            results = [result async for result in search_func(session, terms)]

        localizer = self.localizer.for_message('confess__search')
        source = ConfessionSearchSource(
            results, type=confession.type, per_page=20, localizer=localizer
        )
        pages = UIPages(ctx, source, localizer=localizer)
        await pages.start()


class _SectionInfo(NamedTuple):
    section: str
    text: str
    text_lower: str
    text_ellipsized: str


def _create_section_info(section: str, title: str, /) -> _SectionInfo:
    text = f'{section}. {title}'
    return _SectionInfo(
        section=section,
        text=text,
        text_lower=text.lower(),
        text_ellipsized=ellipsize(text, max_length=100),
    )


@define
class _ConfessionOption:
    command: str
    command_lower: str
    name: str
    name_lower: str
    type: ConfessionTypeEnum
    section_info: list[_SectionInfo]

    @property
    def key(self) -> str:
        return self.command

    def matches(self, text: str, /) -> bool:
        return text in self.name_lower or text in self.command_lower

    def choice(self) -> app_commands.Choice[str]:
        return app_commands.Choice(name=self.name, value=self.command)

    @classmethod
    def create(
        cls,
        confession: ConfessionRecord,
        section_info: list[_SectionInfo],
        /,
    ) -> Self:
        return cls(
            name=confession.name,
            name_lower=confession.name.lower(),
            command=confession.command,
            command_lower=confession.command.lower(),
            type=confession.type,
            section_info=section_info,
        )


@define(eq=False)
class ConfessionAutoCompleter(AutoCompleter[_ConfessionOption]):
    create_option: Callable[[ConfessionRecord], _ConfessionOption] = field(
        default=_ConfessionOption.create
    )


@define(eq=False)
class SectionAutoCompleter(app_commands.Transformer):
    confession_lookup: ConfessionAutoCompleter

    async def transform(self, interaction: discord.Interaction, value: str) -> str:
        return value

    async def autocomplete(  # type: ignore
        self, interaction: discord.Interaction, value: str
    ) -> list[app_commands.Choice[str]]:
        value = value.lower().strip()

        if (
            interaction.data is None
            or (options := interaction.data.get('options')) is None
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
                name=section_info.text_ellipsized, value=section_info.section
            )
            for section_info in item.section_info
            if not value
            or value in section_info.text_lower
            or value in section_info.section
        ][:25]


_confession_lookup = ConfessionAutoCompleter()
_section_lookup = SectionAutoCompleter(_confession_lookup)


class ConfessionAppCommands(
    ConfessionBase,
    GroupCog['Erasmus'],
    group_name='confess',
    group_description='Confessions',
):
    async def cog_load(self) -> None:
        async with Session() as session:
            async for confession in ConfessionRecord.get_all(session):
                format_number = _number_formatters[confession.numbering]
                match confession.type:
                    case ConfessionTypeEnum.CHAPTERS:
                        section_info = [
                            _create_section_info(
                                f'{format_number(paragraph.chapter_number)}.'
                                f'{format_number(paragraph.paragraph_number)}',
                                paragraph.chapter.chapter_title,
                            )
                            async for paragraph in confession.get_paragraphs(session)
                        ]
                    case ConfessionTypeEnum.ARTICLES:
                        section_info = [
                            _create_section_info(
                                format_number(article.article_number), article.title
                            )
                            async for article in confession.get_articles(session)
                        ]
                    case ConfessionTypeEnum.QA:
                        section_info = [
                            _create_section_info(
                                format_number(question.question_number),
                                question.question_text,
                            )
                            async for question in confession.get_questions(session)
                        ]

                _confession_lookup.add(
                    _ConfessionOption.create(confession, section_info)
                )

    async def cog_unload(self) -> None:
        _confession_lookup.clear()

    @app_commands.command()
    @app_commands.checks.cooldown(
        rate=2, per=30.0, key=lambda i: (i.guild_id, i.user.id)
    )
    @app_commands.describe(
        source='The confession or catechism to search in', terms='Terms to search for'
    )
    async def search(
        self,
        interaction: discord.Interaction,
        /,
        source: app_commands.Transform[str, _confession_lookup],
        terms: str,
    ) -> None:
        '''Search for terms in a confession or catechism'''

        async with Session() as session:
            confession = await ConfessionRecord.get_by_command(session, source)

            match confession.type:
                case ConfessionTypeEnum.CHAPTERS:
                    search_func: Callable[
                        [AsyncSession, Sequence[str]],
                        AsyncIterator[ConfessionSearchResult],
                    ] = confession.search_paragraphs
                case ConfessionTypeEnum.ARTICLES:
                    search_func = confession.search_articles
                case ConfessionTypeEnum.QA:
                    search_func = confession.search_questions

            results = [
                result async for result in search_func(session, terms.split(' '))
            ]

        localizer = self.localizer.for_message('confess__search', interaction.locale)
        search_source = ConfessionSearchSource(
            results,
            type=confession.type,
            per_page=20,
            localizer=localizer,
        )
        pages = UIPages(interaction, search_source, localizer=localizer)
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
        interaction: discord.Interaction,
        /,
        source: app_commands.Transform[str, _confession_lookup],
        section: app_commands.Transform[str, _section_lookup],
    ) -> None:
        '''Cite a section from a confession or catechism'''

        async with Session() as session:
            confession = await ConfessionRecord.get_by_command(session, source)

        if (match := _reference_res[confession.type].match(section)) is None:
            raise NoSectionError(confession.name, section, confession.type)

        await self._show_citation(interaction, confession, match)


async def setup(bot: Erasmus, /) -> None:
    await bot.add_cog(Confession(bot))
    await bot.add_cog(ConfessionAppCommands(bot))

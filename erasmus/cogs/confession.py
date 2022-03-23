from __future__ import annotations

from collections.abc import AsyncIterator, Callable, Sequence
from re import Match
from typing import Any, Final, Optional, Union, cast

import discord
from botus_receptus import Cog, re
from botus_receptus.formatting import (
    EmbedPaginator,
    bold,
    escape,
    pluralizer,
    underline,
)
from discord import app_commands
from discord.ext import commands

from ..context import Context
from ..db.confession import Article
from ..db.confession import Confession as ConfessionRecord
from ..db.confession import ConfessionTypeEnum, NumberingTypeEnum, Paragraph, Question
from ..erasmus import Erasmus
from ..exceptions import InvalidConfessionError, NoSectionError, NoSectionsError
from ..format import int_to_roman, roman_to_int
from ..page_source import EmbedPageSource, ListPageSource
from ..ui_pages import ContextUIPages

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


ConfessionSearchResult = Union[Paragraph, Article, Question]


class ConfessionSearchSource(
    EmbedPageSource[Sequence[ConfessionSearchResult]],
    ListPageSource[ConfessionSearchResult],
):
    entry_text_string: str

    def __init__(
        self,
        entries: list[ConfessionSearchResult],
        /,
        *,
        per_page: int,
        type: ConfessionTypeEnum,
    ) -> None:
        super().__init__(entries, per_page=per_page)

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
            self.embed.description = 'I found 0 results'
            return

        lines: list[str] = []

        for entry in entries:
            lines.append(self.entry_text_string.format(entry=entry))

        self.embed.description = '\n'.join(lines)


class ConfessionBase(Cog):
    bot: Erasmus

    def __init__(self, bot: Erasmus, /) -> None:
        self.bot = bot


class Confession(ConfessionBase):
    async def cog_command_error(self, ctx: Context, error: Exception, /) -> None:  # type: ignore  # noqa: B950
        if (
            isinstance(
                error,
                (
                    commands.CommandInvokeError,
                    commands.BadArgument,
                    commands.ConversionError,
                ),
            )
            and error.__cause__ is not None
        ):
            error = cast(Exception, error.__cause__)

        if isinstance(error, InvalidConfessionError):
            message = f'`{error.confession}` is not a valid confession.'
        elif isinstance(error, NoSectionError):
            message = (
                f'`{error.confession}` does not have '
                f'{"an" if error.section_type == "article" else "a"} '
                f'{error.section_type} `{error.section}`'
            )
        elif isinstance(error, NoSectionsError):
            message = f'`{error.confession}` has no {error.section_type}'
        else:
            return

        await ctx.send_error(escape(message, mass_mentions=True))

    @commands.command(brief='Query confessions and catechisms', help=_confess_help)
    @commands.cooldown(rate=10, per=30.0, type=commands.BucketType.user)
    async def confess(
        self, ctx: Context, confession: Optional[str] = None, /, *args: str
    ) -> None:
        if confession is None:
            await self.list(ctx)
            return

        row = await ConfessionRecord.get_by_command(confession)

        if len(args) == 0:
            await self.list_contents(ctx, row)
            return

        if not (match := _reference_res[row.type].match(args[0])):
            await self.search(ctx, row, *args)
            return

        await self.show_item(ctx, row, match)

    async def list(self, ctx: Context, /) -> None:
        paginator = EmbedPaginator()
        paginator.add_line('I support the following confessions:', empty=True)

        async for conf in ConfessionRecord.get_all():
            paginator.add_line(f'  `{conf.command}`: {conf.name}')

        for page in paginator:
            await ctx.send_embed(page)

    async def list_contents(
        self,
        ctx: Context,
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
        ctx: Context,
        confession: ConfessionRecord,
        /,
    ) -> None:
        paginator = EmbedPaginator()
        getter: Callable[[], AsyncIterator[Any]] | None = None
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
        async for record in getter():
            paginator.add_line(
                '**{number}**. {title}'.format(
                    number=format_number(getattr(record, number_key)),
                    title=getattr(record, title_key),
                )
            )

        for index, page in enumerate(paginator):
            await ctx.send_embed(
                page, title=(underline(bold(confession.name)) if index == 0 else None)
            )

    async def list_questions(
        self,
        ctx: Context,
        confession: ConfessionRecord,
        /,
    ) -> None:
        count = await confession.get_question_count()
        question_str = _pluralizers[ConfessionTypeEnum.QA](count)

        await ctx.send_embed(f'`{confession.name}` has {question_str}')

    async def search(
        self, ctx: Context, confession: ConfessionRecord, /, *terms: str
    ) -> None:
        if confession.type == ConfessionTypeEnum.CHAPTERS:
            search_func: Callable[
                [Sequence[str]], AsyncIterator[ConfessionSearchResult]
            ] = confession.search_paragraphs
        elif confession.type == ConfessionTypeEnum.ARTICLES:
            search_func = confession.search_articles
        else:  # ConfessionTypeEnum.QA
            search_func = confession.search_questions

        source = ConfessionSearchSource(
            [result async for result in search_func(terms)],
            type=confession.type,
            per_page=20,
        )
        pages = ContextUIPages(source, ctx=ctx)
        await pages.start()

    async def show_item(
        self,
        ctx: Context,
        confession: ConfessionRecord,
        match: Match[str],
        /,
    ) -> None:
        title: str | None = None
        output: str | None = None

        paginator = EmbedPaginator()
        format_number = _number_formatters[confession.numbering]

        if confession.type == ConfessionTypeEnum.CHAPTERS:
            if match['chapter_roman']:
                chapter_num = roman_to_int(match['chapter_roman'])
                paragraph_num = roman_to_int(match['paragraph_roman'])
            else:
                chapter_num = int(match['chapter'])
                paragraph_num = int(match['paragraph'])

            paragraph = await confession.get_paragraph(chapter_num, paragraph_num)

            paragraph_number = format_number(paragraph.paragraph_number)
            chapter_number = format_number(paragraph.chapter.chapter_number)
            title = underline(
                bold(f'{chapter_number}. {paragraph.chapter.chapter_title}')
            )
            output = f'**{paragraph_number}.** {paragraph.text}'

        elif confession.type == ConfessionTypeEnum.QA:
            q_or_a = match['qa']
            if match['number_roman']:
                question_number = roman_to_int(match['number_roman'])
            else:
                question_number = int(match['number'])

            question = await confession.get_question(question_number)

            question_number_str = format_number(question_number)

            if q_or_a is None:
                title = underline(
                    bold(f'{question_number_str}. {question.question_text}')
                )
                output = f'{question.answer_text}'
            elif q_or_a.lower() == 'q':
                output = f'**Q{question_number_str}**. {question.question_text}'
            else:
                output = f'**A{question_number_str}**: {question.answer_text}'

        elif confession.type == ConfessionTypeEnum.ARTICLES:
            if match['article_roman']:
                article_number = roman_to_int(match['article_roman'])
            else:
                article_number = int(match['article'])

            article = await confession.get_article(article_number)

            title = underline(bold(f'{format_number(article_number)}. {article.title}'))
            output = article.text

        if output:
            paginator.add_line(output)

        for page in paginator:
            await ctx.send_embed(page, title=title)
            title = None


class ConfessionAppCommands(ConfessionBase):
    async def cog_load(self) -> None:
        async for conf in ConfessionRecord.get_all():
            self.__add_confession(conf)

    confess = app_commands.Group(name='confess', description='Confessions')

    def __add_confession(self, confession: ConfessionRecord, /) -> None:
        command = app_commands.Command(
            name=confession.command,
            description=confession.name,
            callback=ConfessionAppCommands.__confess_callback,
        )
        command.binding = self
        self.confess.add_command(command)

    @app_commands.describe(ref_or_search='The section or search terms')
    async def __confess_callback(
        self, interaction: discord.Interaction, ref_or_search: str
    ) -> None:
        assert interaction.command is not None
        print(interaction.command.name)

        confession = await ConfessionRecord.get_by_command(interaction.command.name)
        print(confession)

        await interaction.response.send_message('blah')


async def setup(bot: Erasmus, /) -> None:
    await bot.add_cog(Confession(bot))
    await bot.add_cog(ConfessionAppCommands(bot))

from typing import List, Callable, Sequence, Any, Match, Awaitable, Optional

import attr
from discord.ext import commands
from asyncpg import Connection
from botus_receptus.formatting import pluralizer, PluralizerType, bold, underline, EmbedPaginator
from botus_receptus import re

from ..db import (
    ConfessionType, Confession as ConfessionRow, get_confessions, get_confession, get_chapters,
    get_paragraph, search_paragraphs, search_questions, get_question_count, get_question,
    get_articles, get_article, search_articles, NumberingType
)
from ..format import int_to_roman, roman_to_int  # noqa: F401

from ..erasmus import Erasmus
from ..context import Context

pluralize_match = pluralizer('match', 'es')

_roman_re = re.group(re.between(0, 4, 'M'),
                     re.either('CM',
                               'CD',
                               re.group(re.optional('D'),
                                        re.between(0, 3, 'C'))),
                     re.either('XC',
                               'XL',
                               re.group(re.optional('L'),
                                        re.between(0, 3, 'X'))),
                     re.either('IX',
                               'IV',
                               re.group(re.optional('V'),
                                        re.between(0, 3, 'I'))))

reference_res = {
    ConfessionType.CHAPTERS: re.compile(re.START,
                                        re.either(re.group(re.named_group('chapter')(re.one_or_more(re.DIGITS)),
                                                           re.DOT,
                                                           re.named_group('paragraph')(re.one_or_more(re.DIGITS))),
                                                  re.group(re.named_group('chapter_roman')(_roman_re),
                                                           re.DOT,
                                                           re.named_group('paragraph_roman')(_roman_re))),
                                        re.END),
    ConfessionType.QA: re.compile(re.START,
                                  re.optional(re.named_group('qa')('[qaQA]')),
                                  re.either(re.named_group('number')(re.one_or_more(re.DIGITS)),
                                            re.named_group('number_roman')(_roman_re)),
                                  re.END),
    ConfessionType.ARTICLES: re.compile(re.START,
                                        re.either(re.named_group('article')(re.one_or_more(re.DIGITS)),
                                                  re.named_group('article_roman')(_roman_re)),
                                        re.END)
}

pluralizers = {
    ConfessionType.CHAPTERS: pluralizer('paragraph'),
    ConfessionType.ARTICLES: pluralizer('article'),
    ConfessionType.QA: pluralizer('question')
}

number_formatters = {
    NumberingType.ARABIC: lambda n: str(n),
    NumberingType.ROMAN: int_to_roman
}


confess_help = '''
Arguments:
----------
    [confession] - A confession to query. Can be found by invoking {prefix}confess with no arguments.

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


@attr.s(slots=True, auto_attribs=True)
class Confession(object):
    bot: Erasmus

    @commands.command(brief='Query confessions and catechisms', help=confess_help)
    @commands.cooldown(rate=10, per=30.0, type=commands.BucketType.user)
    async def confess(self, ctx: Context, confession: Optional[str] = None, *args: str) -> None:
        if confession is None:
            await self.list(ctx)
            return

        row = await get_confession(ctx.db, confession)

        if len(args) == 0:
            await self.list_contents(ctx, row)
            return

        match = reference_res[row['type']].match(args[0])

        if not match:
            await self.search(ctx, row, *args)
            return

        await self.show_item(ctx, row, match)

    async def list(self, ctx: Context) -> None:
        paginator = EmbedPaginator()
        paginator.add_line('I support the following confessions:', empty=True)

        confs = await get_confessions(ctx.db)
        for conf in confs:
            paginator.add_line(f'  `{conf["command"]}`: {conf["name"]}')

        for page in paginator:
            await ctx.send_embed(page)

    async def list_contents(self, ctx: Context, confession: ConfessionRow) -> None:
        if confession['type'] == ConfessionType.CHAPTERS or confession['type'] == ConfessionType.ARTICLES:
            await self.list_sections(ctx, confession)
        elif confession['type'] == ConfessionType.QA:
            await self.list_questions(ctx, confession)

    async def list_sections(self, ctx: Context, confession: ConfessionRow) -> None:
        paginator = EmbedPaginator()
        getter: Optional[Callable[[Connection, ConfessionRow], Awaitable[List[Any]]]] = None
        number_key: Optional[str] = None
        title_key: Optional[str] = None

        if confession['type'] == ConfessionType.CHAPTERS:
            getter = get_chapters
            number_key = 'chapter_number'
            title_key = 'chapter_title'
        else:  # ConfessionType.ARTICLES
            getter = get_articles
            number_key = 'article_number'
            title_key = 'title'

        format_number = number_formatters[confession['numbering']]
        records = await getter(ctx.db, confession)
        for record in records:
            paginator.add_line('**{number}**. {title}'.format(number=format_number(record[number_key]),
                                                              title=record[title_key]))

        for index, page in enumerate(paginator):
            await ctx.send_embed(page, title=(underline(bold(confession["name"])) if index == 0 else None))

    async def list_questions(self, ctx: Context, confession: ConfessionRow) -> None:
        count = await get_question_count(ctx.db, confession)
        question_str = pluralizers[ConfessionType.QA](count)

        await ctx.send_embed(f'`{confession["name"]}` has {question_str}')

    async def search(self, ctx: Context, confession: ConfessionRow, *terms: str) -> None:
        pluralize_type: Optional[PluralizerType] = None
        references: Optional[List[str]] = []
        reference_pattern: Optional[str] = None
        search_func: Optional[Callable[[Connection, ConfessionRow, Sequence[str]], Awaitable[List[Any]]]] = None
        paginate = True

        pluralize_type = pluralizers[confession['type']]

        if confession['type'] == ConfessionType.CHAPTERS:
            reference_pattern = '{chapter_number}.{paragraph_number}'
            search_func = search_paragraphs
            paginate = False
        elif confession['type'] == ConfessionType.ARTICLES:
            reference_pattern = '**{article_number}**. {title}'
            search_func = search_articles
        else:  # ConfessionType.QA
            reference_pattern = '**{question_number}**. {question_text}'
            search_func = search_questions

        results = await search_func(ctx.db, confession, terms)
        references = [reference_pattern.format(**result) for result in results]

        matches = pluralize_match(len(references))
        first_line = f'I have found {matches}'

        num_references = len(references)
        if num_references > 0:
            first_line += ' in the following {}:' \
                .format(pluralize_type(num_references, include_number=False))

        if paginate:
            paginator = EmbedPaginator()
            paginator.add_line(first_line, empty=num_references > 0)

            for reference in references:
                paginator.add_line(reference)

            for page in paginator:
                await ctx.send_embed(page)
        else:
            if num_references > 0:
                first_line += '\n\n' + ', '.join(references)

            await ctx.send_embed(first_line)

    async def show_item(self, ctx: Context, confession: ConfessionRow, match: Match[str]) -> None:
        title: Optional[str] = None
        output: Optional[str] = None

        paginator = EmbedPaginator()
        format_number = number_formatters[confession['numbering']]

        if confession['type'] == ConfessionType.CHAPTERS:
            if match['chapter_roman']:
                chapter_num = roman_to_int(match['chapter_roman'])
                paragraph_num = roman_to_int(match['paragraph_roman'])
            else:
                chapter_num = int(match['chapter'])
                paragraph_num = int(match['paragraph'])

            paragraph = await get_paragraph(ctx.db, confession, chapter_num, paragraph_num)

            paragraph_number = format_number(paragraph['paragraph_number'])
            chapter_number = format_number(paragraph['chapter_number'])
            title = underline(bold(f'{chapter_number}. {paragraph["chapter_title"]}'))
            output = f'**{paragraph_number}.** {paragraph["text"]}'

        elif confession['type'] == ConfessionType.QA:
            q_or_a = match['qa']
            if match['number_roman']:
                question_number = roman_to_int(match['number_roman'])
            else:
                question_number = int(match['number'])

            question = await get_question(ctx.db, confession, question_number)

            question_number_str = format_number(question_number)

            if q_or_a is None:
                title = underline(bold(f'{question_number_str}. {question["question_text"]}'))
                output_str = '{answer_text}'
            elif q_or_a.lower() == 'q':
                output_str = '**Q{question_number_str}**. {question_text}'
            else:
                output_str = '**A{question_number_str}**: {answer_text}'

            output = output_str.format(**question)

        elif confession['type'] == ConfessionType.ARTICLES:
            if match['article_roman']:
                article_number = roman_to_int(match['article_roman'])
            else:
                article_number = int(match['article'])

            article = await get_article(ctx.db, confession, article_number)

            title = underline(bold(f'{format_number(article_number)}. {article["title"]}'))
            output = article['text']

        if output:
            paginator.add_line(output)

        for page in paginator:
            await ctx.send_embed(page, title=title)
            title = None


def setup(bot: 'Erasmus') -> None:
    bot.add_cog(Confession(bot))

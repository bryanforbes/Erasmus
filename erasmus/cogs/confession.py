from typing import TYPE_CHECKING, List  # noqa

import discord
from discord.ext import commands

from ..db import (
    ConfessType, ConfessionRow, get_confessions, get_confession, get_chapters,
    get_paragraph, search_paragraphs, search_qas, get_question_count, get_question
)
from ..format import pluralizer
from .. import re

if TYPE_CHECKING:  # pragma: no cover
    from ..erasmus import Erasmus  # noqa
    from ..context import Context  # noqa

pluralize_match = pluralizer('match', 'es')
pluralize_paragraph = pluralizer('paragraph', 's')
pluralize_question = pluralizer('question', 's')
pluralize_article = pluralizer('article', 's')

reference_res = {
    ConfessType.CHAPTERS: re.compile(re.START,
                                     re.named_group('chapter')(re.one_or_more(re.DIGITS)),
                                     re.DOT,
                                     re.named_group('paragraph')(re.one_or_more(re.DIGITS)),
                                     re.END),
    ConfessType.QA: re.compile(re.START,
                               re.optional(re.named_group('qa')('[qaQA]')),
                               re.named_group('number')(re.one_or_more(re.DIGITS)),
                               re.END),
    ConfessType.ARTICLES: re.compile(re.START,
                                     re.named_group('article')(re.one_or_more(re.DIGITS)),
                                     re.END)
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


class Paginator(commands.Paginator):
    def __init__(self, prefix: str = '', suffix: str = '', max_size: int = 2048) -> None:
        super().__init__(prefix, suffix, max_size)


class Confession(object):
    __slots__ = ('bot')

    bot: 'Erasmus'

    def __init__(self, bot: 'Erasmus') -> None:
        self.bot = bot

    @commands.command(brief='Query confessions', help=confess_help)
    @commands.cooldown(rate=4, per=30.0, type=commands.BucketType.user)
    async def confess(self, ctx: 'Context', confession: str = None, *args: str) -> None:
        if confession is None:
            await self.list(ctx)
            return

        row = await get_confession(confession)

        if not row:
            await ctx.send_error_to_author(f'`{confession}` is not a valid confession.')
            return

        if len(args) == 0:
            if row['type'] == ConfessType.CHAPTERS:
                await self.chapters(ctx, row)
            elif row['type'] == ConfessType.QA:
                await self.questions(ctx, row)
            return

        match = reference_res[row['type']].match(args[0])

        if not match:
            await self.search(ctx, row, *args)
            return

        embed = None  # type: discord.Embed
        output = None  # type: str

        if row['type'] == ConfessType.CHAPTERS:
            paragraph = await get_paragraph(row, int(match['chapter']), int(match['paragraph']))
            if not paragraph:
                await ctx.send_error_to_author(f'{row["name"]} does not have a paragraph {args[0]}')
                return

            embed = discord.Embed(title=f'__**{paragraph["chapter_number"]}. {paragraph["chapter_title"]}**__')
            output = f'**{paragraph["paragraph_number"]}.** {paragraph["text"]}'

        elif row['type'] == ConfessType.QA:
            q_or_a = match['qa']
            question_number = int(match['number'])
            question = await get_question(row, question_number)

            if q_or_a is None:
                embed = discord.Embed(title=f'__**{question["question_number"]}. {question["question_text"]}**__')
                output_str = '{answer_text}'
            elif q_or_a.lower() == 'q':
                output_str = '**Q{question_number}**. {question_text}'
            else:
                output_str = '**A{question_number}**: {answer_text}'

            output = output_str.format(**question)

        await ctx.send_to_author(output, embed=embed)

    async def list(self, ctx: 'Context') -> None:
        paginator = Paginator()
        paginator.add_line('I support the following confessions:', empty=True)

        async with get_confessions() as confs:
            async for conf in confs:
                paginator.add_line(f'  `{conf["command"]}`: {conf["name"]}')

        await ctx.send_pages_to_author(paginator.pages)

    async def chapters(self, ctx: 'Context', confession: ConfessionRow) -> None:
        paginator = Paginator()

        async with get_chapters(confession) as chapters:
            async for chapter in chapters:
                paginator.add_line(f'**{chapter["chapter_number"]}**. {chapter["chapter_title"]}')

        if len(paginator.pages) == 0:
            await ctx.send_error_to_author(f'`{confession["name"]}` has no chapters')

        embed = discord.Embed(title=f'__**{confession["name"]}**__')

        await ctx.send_pages_to_author(paginator.pages, embed=embed)

    async def questions(self, ctx: 'Context', confession: ConfessionRow) -> None:
        count = await get_question_count(confession)
        question_str = pluralize_question(count)

        await ctx.send_to_author(f'`{confession["name"]}` has {question_str}')

    async def search(self, ctx: 'Context', confession: ConfessionRow, *terms: str) -> None:
        references_str = None  # type: str
        references = []  # type: List[str]
        reference_type = None  # type: str

        if confession['type'] == ConfessType.CHAPTERS or confession['type'] == ConfessType.ARTICLES:
            if confession['type'] == ConfessType.CHAPTERS:
                reference_pluralizer = pluralize_paragraph
                reference_pattern = '{chapter}.{paragraph}'
            else:
                reference_pluralizer = pluralize_article
                reference_pattern = '{paragraph}'

            async with search_paragraphs(confession, terms) as chapter_results:
                references = [reference_pattern.format(chapter=result['chapter_number'],
                                                       paragraph=result['paragraph_number'])
                              async for result in chapter_results]

            reference_type = reference_pluralizer(len(references), include_number=False)
            references_str = ', '.join(references)

            matches = pluralize_match(len(references))
            output = f'I have found {matches}'

            if len(references) > 0:
                output += f' in the following {reference_type}:\n\n'
                output += references_str

            await ctx.send_to_author(output)

        elif confession['type'] == ConfessType.QA:
            paginator = Paginator()
            async with search_qas(confession, terms) as qa_results:
                references = [f'**{result["question_number"]}**. {result["question_text"]}'
                              async for result in qa_results]

            matches = pluralize_match(len(references))
            output = f'I have found {matches}'

            if len(references) > 0:
                output += ' in the following {}:'.format(pluralize_question(len(references), include_number=False))

            paginator.add_line(output, empty=True)

            for reference in references:
                paginator.add_line(reference)

            await ctx.send_pages_to_author(paginator.pages)


def setup(bot: 'Erasmus') -> None:
    bot.add_cog(Confession(bot))

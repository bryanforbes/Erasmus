from typing import TYPE_CHECKING, List, AsyncIterable  # noqa
from mypy_extensions import TypedDict

import discord
from discord.ext import commands
from asyncpgsa import pg  # type: ignore
import sqlalchemy as sa  # type: ignore

from ..db import confessions, confession_chapters, confession_paragraphs
from ..format import pluralizer
from .. import re

if TYPE_CHECKING:  # pragma: no cover
    from ..erasmus import Erasmus  # noqa
    from ..context import Context  # noqa

pluralize_match = pluralizer('match', 'es')

chapters_select = sa.select([confession_chapters.c.chapter_number,
                             confession_chapters.c.title]) \
    .select_from(confession_chapters.join(confessions)) \
    .order_by(confession_chapters.c.chapter_number.asc())

paragraph_select = sa.select([confession_chapters.c.title,
                              confession_paragraphs.c.chapter_number,
                              confession_paragraphs.c.paragraph_number,
                              confession_paragraphs.c.text]) \
    .select_from(confession_paragraphs.join(confessions).join(confession_chapters))

paragraph_search = sa.select([confession_paragraphs.c.chapter_number,
                              confession_paragraphs.c.paragraph_number]) \
    .select_from(confession_paragraphs.join(confessions))

reference_re = re.compile(re.START,
                          re.named_group('chapter')(re.one_or_more(re.DIGITS)),
                          re.DOT,
                          re.named_group('paragraph')(re.one_or_more(re.DIGITS)),
                          re.END)


class ConfessionRow(TypedDict):
    id: int
    command: str
    name: str


class ChapterRow(TypedDict):
    chapter_number: int
    title: str


class SearchRow(TypedDict):
    chapter_number: int
    paragraph_number: int


class ParagraphRow(SearchRow):
    title: str
    text: str


confess_help = '''
Arguments:
----------
    [confession] - A confession to query. Can be found by invoking {prefix}confess with no arguments.

    [args...] - Arguments to pass to query or look up in the confession.

Examples:
---------
    List all confessions:
        {prefix}confess

    List the chapters of a confession:
        {prefix}confess 1689

    Search for terms in a confession:
        {prefix}confess 1689 faith hope

    Look up the paragraph of a confession:
        {prefix}confess 1689 2.2
'''


class Confession(object):
    __slots__ = ('bot')

    bot: 'Erasmus'

    def __init__(self, bot: 'Erasmus') -> None:
        self.bot = bot

    @commands.command(brief='Query confessions', help=confess_help)
    async def confess(self, ctx: 'Context', confession: str = None, *args: str) -> None:
        if confession is None:
            await self.list(ctx)
            return

        row = await pg.fetchrow(confessions.select().where(confessions.c.command == confession))  # type: ConfessionRow

        if not row:
            await ctx.send_error_to_author(f'`{confession}` is not a valid confession.')
            return

        if len(args) == 0:
            await self.chapters(ctx, row)
            return

        match = reference_re.match(args[0])

        if not match:
            await self.search(ctx, row, *args)
            return

        query = paragraph_select \
            .where(confessions.c.id == row['id']) \
            .where(confession_paragraphs.c.chapter_number == int(match['chapter'])) \
            .where(confession_paragraphs.c.paragraph_number == int(match['paragraph']))

        paragraph = await pg.fetchrow(query)  # type: ParagraphRow

        if not paragraph:
            await ctx.send_error_to_author(f'{row["name"]} does not have a paragraph {args[0]}')
            return

        embed = discord.Embed(title=f'__**{paragraph["chapter_number"]}. {paragraph["title"]}**__')
        await ctx.send_to_author(f'**{paragraph["paragraph_number"]}.** {paragraph["text"]}', embed=embed)

    async def list(self, ctx: 'Context') -> None:
        lines = ['I support the following confessions:', '']

        query = confessions.select().order_by(confessions.c.command.asc())

        async with pg.query(query) as confs:  # type: AsyncIterable[ConfessionRow]
            lines += [f'  `{conf["command"]}`: {conf["name"]}' async for conf in confs]

        output = '\n'.join(lines)
        await ctx.send_to_author(f'\n{output}\n')

    async def chapters(self, ctx: 'Context', confession: ConfessionRow) -> None:
        lines = []  # type: List[str]

        query = chapters_select.where(confessions.c.id == confession['id'])

        async with pg.query(query) as chapters:  # type: AsyncIterable[ChapterRow]
            lines = [f'**{chapter["chapter_number"]}**. {chapter["title"]}' async for chapter in chapters]

        if len(lines) == 0:
            await ctx.send_error_to_author(f'`{confession}` has no chapters')

        embed = discord.Embed(title=f'__**{confession["name"]}**__')

        await ctx.send_to_author('\n'.join(lines), embed=embed)

    async def search(self, ctx: 'Context', confession: ConfessionRow, *terms: str) -> None:
        references = []  # type: List[str]

        query = paragraph_search \
            .where(confessions.c.id == confession['id']) \
            .where(sa.and_(*[confession_paragraphs.c.text.ilike(f'%{term}%') for term in terms]))

        async with pg.query(query) as results:  # AsyncIterable[SearchRow]
            references = [f'{result["chapter_number"]}.{result["paragraph_number"]}'
                          async for result in results]

        matches = pluralize_match(len(references))
        output = f'I have found {matches}'

        if len(references) > 0:
            output += ' in the following paragraphs:\n\n'
            output += ', '.join(references)

        await ctx.send_to_author(output)


def setup(bot: 'Erasmus') -> None:
    bot.add_cog(Confession(bot))

from typing import TYPE_CHECKING, List  # noqa

from discord.ext import commands
from asyncpgsa import pg  # type: ignore
import sqlalchemy as sa  # type: ignore

from ..db import confessions, confession_chapters, confession_paragraphs
from .. import re

if TYPE_CHECKING:  # pragma: no cover
    from ..erasmus import Erasmus  # noqa
    from ..context import Context  # noqa


chapters_select = sa.select([confession_chapters.c.chapter_number,
                             confession_chapters.c.title]) \
    .select_from(confession_chapters.join(confessions)) \
    .order_by(confession_chapters.c.chapter_number.asc())

paragraph_select = sa.select([confession_paragraphs.c.chapter_number,
                              confession_paragraphs.c.paragraph_number,
                              confession_paragraphs.c.text]) \
    .select_from(confession_paragraphs.join(confessions))

reference_re = re.compile(re.START,
                          re.named_group('chapter')(re.one_or_more(re.DIGITS)),
                          re.DOT,
                          re.named_group('paragraph')(re.one_or_more(re.DIGITS)),
                          re.END)


class Confession(object):
    __slots__ = ('bot')

    bot: 'Erasmus'

    def __init__(self, bot: 'Erasmus') -> None:
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def confess(self, ctx: 'Context', confession: str, reference: str = None) -> None:
        match = reference_re.match(reference)

        if not match:
            return

        paragraph = await pg.fetchrow(paragraph_select
                                      .where(confessions.c.command == confession.lower())
                                      .where(confession_paragraphs.c.chapter_number == int(match['chapter']))
                                      .where(confession_paragraphs.c.paragraph_number == int(match['paragraph'])))

        if not paragraph:
            return

        await ctx.send_to_author(paragraph['text'])

    @confess.command()
    async def list(self, ctx: 'Context') -> None:
        lines = ['I support the following confessions:', '']

        async with pg.query(confessions.select()
                            .order_by(confessions.c.command.asc())) as confs:
            lines += [f'  `{conf["command"]}`: {conf["name"]}' async for conf in confs]

        output = '\n'.join(lines)
        await ctx.send_to_author(f'\n{output}\n')

    @confess.command()
    async def chapters(self, ctx: 'Context', confession: str) -> None:
        lines = []  # type: List[str]

        async with pg.query(chapters_select.where(confessions.c.command == confession.lower())) as chapters:
            lines = [f'{chapter["chapter_number"]}. {chapter["title"]}' async for chapter in chapters]

        if len(lines) == 0:
            await ctx.send_error_to_author(f'`{confession}` is not a valid confession.')
            return

        await ctx.send_to_author('\n'.join(lines))

    @confess.command()
    async def search(self, ctx: 'Context', confession: str, *terms: str) -> None:
        references = []  # type: List[str]

        async with pg.query(paragraph_select
                            .where(confessions.c.command == confession.lower())
                            .where(sa.and_(*[confession_paragraphs.c.text.ilike(f'%{term}%') for term in terms]))) \
                as results:
            references = [f'{result["chapter_number"]}.{result["paragraph_number"]}' async for result in results]

        if len(references) > 0:
            await ctx.send_to_author(', '.join(references))


def setup(bot: 'Erasmus') -> None:
    bot.add_cog(Confession(bot))

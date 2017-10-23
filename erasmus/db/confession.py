from typing import Sequence
from mypy_extensions import TypedDict
from sqlalchemy import select, func  # type: ignore
from asyncpgsa import pg  # type: ignore
from enum import Enum

from .types import AIContextManager
from .tables import (
    confessions, confession_types, chapters, paragraphs, questions, articles,
    numbering_types
)

__all__ = (
    'ConfessionType', 'NumberingType', 'Confession', 'Chapter', 'ParagraphSearchResult',
    'Paragraph', 'QuestionSearchResult', 'Question', 'ArticleSearchResult',
    'Article', 'get_confessions', 'get_confession', 'get_chapters', 'get_paragraph',
    'search_paragraphs', 'get_questions', 'get_question_count', 'get_question',
    'search_questions', 'get_articles', 'get_article', 'search_articles'
)


class ConfessionType(Enum):
    ARTICLES = 'ARTICLES'
    CHAPTERS = 'CHAPTERS'
    QA = 'QA'

    def __repr__(self):
        return '<%s.%s>' % (self.__class__.__name__, self.name)


class NumberingType(Enum):
    ARABIC = 'ARABIC'
    ROMAN = 'ROMAN'

    def __repr__(self):
        return '<%s.%s>' % (self.__class__.__name__, self.name)


class Confession(TypedDict):
    id: int
    command: str
    name: str
    type: ConfessionType
    numbering: NumberingType


class Chapter(TypedDict):
    chapter_number: int
    chapter_title: str


class ParagraphSearchResult(TypedDict):
    chapter_number: int
    paragraph_number: int


class Paragraph(ParagraphSearchResult):
    chapter_title: str
    text: str


class QuestionSearchResult(TypedDict):
    question_number: int
    question_text: str


class Question(QuestionSearchResult):
    answer_text: str


class ArticleSearchResult(TypedDict):
    article_number: int
    title: str


class Article(ArticleSearchResult):
    text: str


_select_confessions = confessions.select().order_by(confessions.c.command.asc())


def get_confessions() -> AIContextManager[Confession]:
    return pg.query(_select_confessions)


_select_confession = select([confessions.c.id,
                             confessions.c.command,
                             confessions.c.name,
                             confession_types.c.value.label('type'),
                             numbering_types.c.numbering]) \
    .select_from(confessions.join(confession_types)
                 .join(numbering_types))


async def get_confession(command: str) -> Confession:
    query = _select_confession.where(confessions.c.command == command.lower())
    row = await pg.fetchrow(query)

    if not row:
        return None

    return Confession(id=row['id'], command=row['command'],
                      name=row['name'], type=ConfessionType[row['type']],
                      numbering=NumberingType[row['numbering']])


_chapters_select = select([chapters.c.chapter_number,
                           chapters.c.chapter_title]) \
    .select_from(chapters.join(confessions)) \
    .order_by(chapters.c.chapter_number.asc())


def get_chapters(confession: Confession) -> AIContextManager[Chapter]:
    return pg.query(_chapters_select.where(confessions.c.id == confession['id']))


_paragraph_select = select([chapters.c.chapter_title,
                            paragraphs.c.chapter_number,
                            paragraphs.c.paragraph_number,
                            paragraphs.c.text]) \
    .select_from(paragraphs.join(confessions).join(chapters))


async def get_paragraph(confession: Confession, chapter: int, paragraph: int) -> Paragraph:
    return await pg.fetchrow(_paragraph_select
                             .where(confessions.c.id == confession['id'])
                             .where(chapters.c.chapter_number == chapter)
                             .where(paragraphs.c.chapter_number == chapter)
                             .where(paragraphs.c.paragraph_number == paragraph))


_paragraph_search = select([paragraphs.c.chapter_number,
                            paragraphs.c.paragraph_number]) \
    .select_from(paragraphs.join(confessions)) \
    .order_by(paragraphs.c.chapter_number.asc())


def search_paragraphs(confession: Confession, terms: Sequence[str]) -> \
        AIContextManager[ParagraphSearchResult]:
    return pg.query(_paragraph_search
                    .where(confessions.c.id == confession['id'])
                    .where(func.to_tsvector('english', paragraphs.c.text)
                           .match(' & '.join(terms), postgresql_regconfig='english')))


_questions_select = select([questions.c.question_number,
                            questions.c.question_text]) \
    .select_from(questions.join(confessions)) \
    .order_by(questions.c.question_number.asc())


def get_questions(confession: Confession) -> AIContextManager[QuestionSearchResult]:
    return pg.query(_questions_select.where(confessions.c.id == confession['id']))


_questions_count = select([func.count(questions.c.id).label('num_questions')])


async def get_question_count(confession: Confession) -> int:
    row = await pg.fetchrow(_questions_count.where(questions.c.confess_id == confession['id']))
    return row['num_questions']


_question_select = select([questions.c.question_number,
                           questions.c.question_text,
                           questions.c.answer_text]) \
    .select_from(questions.join(confessions))


async def get_question(confession: Confession, question_number: int) -> Question:
    return await pg.fetchrow(_question_select
                             .where(confessions.c.id == confession['id'])
                             .where(questions.c.question_number == question_number))


_questions_search = select([questions.c.question_number,
                            questions.c.question_text]) \
    .select_from(questions.join(confessions)) \
    .order_by(questions.c.question_number.asc())


def search_questions(confession: Confession, terms: Sequence[str]) -> AIContextManager[QuestionSearchResult]:
    return pg.query(_questions_search
                    .where(confessions.c.id == confession['id'])
                    .where(func.to_tsvector('english',
                                            questions.c.question_text + ' ' + questions.c.answer_text)
                           .match(' & '.join(terms), postgresql_regconfig='english')))


_articles_select = select([articles.c.article_number,
                           articles.c.title]) \
    .select_from(articles.join(confessions)) \
    .order_by(articles.c.article_number.asc())


def get_articles(confession: Confession) -> AIContextManager[ArticleSearchResult]:
    return pg.query(_articles_select.where(confessions.c.id == confession['id']))


_article_select = select([articles.c.article_number,
                          articles.c.title,
                          articles.c.text]) \
    .select_from(articles.join(confessions))


async def get_article(confession: Confession, article_number: int) -> Article:
    return await pg.fetchrow(_article_select
                             .where(confessions.c.id == confession['id'])
                             .where(articles.c.article_number == article_number))


def search_articles(confession: Confession, terms: Sequence[str]) -> AIContextManager[ArticleSearchResult]:
    return pg.query(_articles_select
                    .where(confessions.c.id == confession['id'])
                    .where(func.to_tsvector('english', articles.c.text)
                           .match(' & '.join(terms), postgresql_regconfig='english')))

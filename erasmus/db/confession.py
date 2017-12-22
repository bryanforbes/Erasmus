from typing import Sequence, List, cast
from mypy_extensions import TypedDict
from asyncpg import Connection
from enum import Enum

from .util import select_all, select_one, search
from ..exceptions import InvalidConfessionError, NoSectionError, NoSectionsError

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


async def get_confessions(db: Connection) -> List[Confession]:
    return await select_all(db, columns=['*'], table='confessions', order_by='command')


async def get_confession(db: Connection, command: str) -> Confession:
    row = await select_one(db, command.lower(),
                           columns=('c.id', 'c.command', 'c.name', 't.value AS type', 'n.numbering'),
                           table='confessions AS c',
                           joins=[('confession_numbering_types AS n', 'c.numbering_id = n.id'),
                                  ('confession_types AS t', 'c.type_id = t.id')],
                           where=['c.command = $1'])

    if not row:
        raise InvalidConfessionError(command)

    return Confession(id=row['id'], command=row['command'],
                      name=row['name'], type=ConfessionType[row['type']],
                      numbering=NumberingType[row['numbering']])


async def get_chapters(db: Connection, confession: Confession) -> List[Chapter]:
    chapters = await select_all(db, confession['id'],
                                columns=('ch.chapter_number', 'ch.chapter_title'),
                                table='confession_chapters AS ch',
                                joins=[('confessions AS c', 'ch.confess_id = c.id')],
                                where=['c.id = $1'],
                                order_by='ch.chapter_number')

    if len(chapters) == 0:
        raise NoSectionsError(confession['name'], 'chapters')

    return chapters


async def get_paragraph(db: Connection, confession: Confession,
                        chapter: int, paragraph: int) -> Paragraph:
    result = await select_one(db, confession['id'], chapter, paragraph,
                              columns=('ch.chapter_title', 'p.chapter_number', 'p.paragraph_number', 'p.text'),
                              table='confession_paragraphs AS p',
                              joins=[('confessions AS c', 'c.id = p.confess_id'),
                                     ('confession_chapters AS ch',
                                      'ch.confess_id = c.id AND ch.chapter_number = p.chapter_number')],
                              where=['c.id = $1',
                                     'p.chapter_number = $2',
                                     'p.paragraph_number = $3'])

    if not result:
        raise NoSectionError(confession['name'], f'{chapter}.{paragraph}', 'paragraph')

    return result


async def search_paragraphs(db: Connection, confession: Confession,
                            terms: Sequence[str]) -> List[ParagraphSearchResult]:
    return await search(db, confession['id'],
                        columns=['p.chapter_number', 'p.paragraph_number'],
                        table='confession_paragraphs AS p',
                        joins=[('confessions AS c', 'c.id = p.confess_id'),
                               ('confession_chapters AS ch',
                                'ch.confess_id = c.id AND ch.chapter_number = p.chapter_number')],
                        where=['c.id = $1'],
                        search_columns=['ch.chapter_title', 'p.text'],
                        terms=terms,
                        order_by='p.chapter_number')


async def get_questions(db: Connection, confession: Confession) -> List[QuestionSearchResult]:
    return await select_all(db, confession['id'],
                            columns=['q.question_number', 'q.question_text'],
                            table='confession_questions AS q',
                            joins=[('confessions AS c', 'c.id = q.confess_id')],
                            where=['c.id = $1'],
                            order_by='q.question_number')


async def get_question_count(db: Connection, confession: Confession) -> int:
    query = '''SELECT count(id) FROM confession_questions WHERE confess_id = $1'''

    return cast(int, await db.fetchval(query, confession['id'], column=0))


async def get_question(db: Connection, confession: Confession, question_number: int) -> Question:
    question = await select_one(db, confession['id'], question_number,
                                columns=['q.question_number', 'q.question_text', 'q.answer_text'],
                                table='confession_questions AS q',
                                joins=[('confessions AS c', 'c.id = q.confess_id')],
                                where=['c.id = $1', 'q.question_number = $2'])

    if not question:
        raise NoSectionError(confession['name'], f'{question_number}', 'question')

    return question


async def search_questions(db: Connection, confession: Confession, terms: Sequence[str]) -> List[QuestionSearchResult]:
    return await search(db, confession['id'],
                        columns=['q.question_number', 'q.question_text'],
                        table='confession_questions AS q',
                        joins=[('confessions AS c', 'c.id = q.confess_id')],
                        where=['c.id = $1'],
                        search_columns=['q.question_text', 'q.answer_text'],
                        terms=terms,
                        order_by='q.question_number')


async def get_articles(db: Connection, confession: Confession) -> List[ArticleSearchResult]:
    articles = await select_all(db, confession['id'],
                                columns=['a.article_number', 'a.title'],
                                table='confession_articles AS a',
                                joins=[('confessions AS c', 'c.id = a.confess_id')],
                                where=['c.id = $1'],
                                order_by='a.article_number')

    if len(articles) == 0:
        raise NoSectionsError(confession['name'], 'articles')

    return articles


async def get_article(db: Connection, confession: Confession, article_number: int) -> Article:
    article = await select_one(db, confession['id'], article_number,
                               columns=['a.article_number', 'a.title', 'a.text'],
                               table='confession_articles AS a',
                               joins=[('confessions AS C', 'c.id = a.confess_id')],
                               where=['c.id = $1', 'a.article_number = $2'])

    if not article:
        raise NoSectionError(confession['name'], f'{article_number}', 'article')

    return article


async def search_articles(db: Connection, confession: Confession, terms: Sequence[str]) -> List[ArticleSearchResult]:
    return await search(db, confession['id'],
                        columns=['a.article_number', 'a.title'],
                        table='confession_articles AS a',
                        joins=[('confessions AS c', 'c.id = a.confess_id')],
                        where=['c.id = $1'],
                        search_columns=['a.title', 'a.text'],
                        terms=terms,
                        order_by='a.article_number')

from typing import AsyncIterable, AsyncContextManager, Sequence, TypeVar
from mypy_extensions import TypedDict
from sqlalchemy import (  # type: ignore
    MetaData, Table, Column, Integer, String, ForeignKey, Boolean, BigInteger,
    Text, Index, func, column, select
)
import sqlalchemy.types as types  # type: ignore
from sqlalchemy.dialects.postgresql import insert  # type: ignore
from asyncpgsa import pg  # type: ignore
from enum import Enum

__all__ = ['insert', 'Snowflake', 'metadata', 'bible_versions', 'guild_bibles',
           'guild_prefs', 'user_prefs', 'confessions', 'confession_chapters',
           'confession_paragraphs']


class Snowflake(types.TypeDecorator):
    impl = types.String

    def process_bind_param(self, value, dialect):
        if not isinstance(value, int):
            raise TypeError(f'expected int, got {type(value).__name__}')

        return str(value)

    def process_result_value(self, value, dialect):
        return int(value)


class ConfessType(Enum):
    ARTICLES = 'ARTICLES'
    CHAPTERS = 'CHAPTERS'
    QA = 'QA'

    def __repr__(self):
        return '<%s.%s>' % (self.__class__.__name__, self.name)


class ConfessValue(types.TypeDecorator):
    impl = types.String

    def process_bind_param(self, value, dialect):
        print('here as well')
        if not isinstance(value, ConfessType):
            raise TypeError(f'expected ConfessType, got {type(value).__name__}')

        return value.value

    def process_result_value(self, value, dialect):
        print('here')
        return ConfessType[value]


metadata = MetaData()

bible_versions = Table('bible_versions', metadata,
                       Column('id', Integer, primary_key=True),
                       Column('command', String, unique=True),
                       Column('name', String),
                       Column('abbr', String),
                       Column('service', String),
                       Column('service_version', String),
                       Column('rtl', Boolean, default=False),
                       Column('books', BigInteger, nullable=False))

guild_bibles = Table('guild_bibles', metadata,
                     Column('guild_id', Snowflake, primary_key=True),
                     Column('bible_id', Integer, ForeignKey('bible_versions.id'), primary_key=True))

guild_prefs = Table('guild_prefs', metadata,
                    Column('guild_id', Snowflake, primary_key=True),
                    Column('prefix', String(1), default='$'))

user_prefs = Table('user_prefs', metadata,
                   Column('user_id', Snowflake, primary_key=True),
                   Column('bible_id', Integer, ForeignKey('bible_versions.id')))

confessions = Table('confessions', metadata,
                    Column('id', Integer, primary_key=True),
                    Column('command', String, unique=True),
                    Column('name', String))

confession_chapters = Table('confession_chapters', metadata,
                            Column('id', Integer, primary_key=True),
                            Column('confession_id', Integer, ForeignKey('confessions.id')),
                            Column('chapter_number', Integer),
                            Column('title', String))

confession_paragraphs = Table('confession_paragraphs', metadata,
                              Column('id', Integer, primary_key=True),
                              Column('confession_id', Integer, ForeignKey('confessions.id')),
                              Column('chapter_number', Integer),
                              Column('paragraph_number', Integer),
                              Column('text', Text),
                              Index('confession_paragraphs_text_idx',
                                    func.to_tsvector('english', column('text')),
                                    postgresql_using='gin'))

confess_types = Table('confess_types', metadata,
                      Column('id', Integer, primary_key=True),
                      Column('value', ConfessValue, unique=True, nullable=False))

confesses = Table('confesses', metadata,
                  Column('id', Integer, primary_key=True),
                  Column('command', String, unique=True),
                  Column('name', String, nullable=False),
                  Column('type_id', Integer,
                         ForeignKey('confess_types.id'), nullable=False))

confess_chapters = Table('confess_chapters', metadata,
                         Column('id', Integer, primary_key=True),
                         Column('confess_id', Integer,
                                ForeignKey('confesses.id'), nullable=False),
                         Column('chapter_number', Integer, nullable=False),
                         Column('chapter_title', String, nullable=False))

confess_paragraphs = Table('confess_paragraphs', metadata,
                           Column('id', Integer, primary_key=True),
                           Column('confess_id', Integer,
                                  ForeignKey('confesses.id'), nullable=False),
                           Column('chapter_number', Integer, nullable=False),
                           Column('paragraph_number', Integer),
                           Column('text', Text, nullable=False),
                           Index('confess_paragraphs_text_idx',
                                 func.to_tsvector('english', 'text'),
                                 postgresql_using='gin'))

confess_qas = Table('confess_qas', metadata,
                    Column('id', Integer, primary_key=True),
                    Column('confess_id', Integer,
                           ForeignKey('confesses.id'), nullable=False),
                    Column('question_number', Integer, nullable=False),
                    Column('question_text', Text, nullable=False),
                    Column('answer_text', Text, nullable=False),
                    Index('confess_qas_text_idx',
                          func.to_tsvector('english', "question_text || ' ' || answer_text"),
                          postgresql_using='gin'))


class ConfessionRow(TypedDict):
    id: int
    command: str
    name: str
    type: ConfessType


class ChapterRow(TypedDict):
    chapter_number: int
    chapter_title: str


class QASearchRow(TypedDict):
    question_number: int
    question_text: str


class QARow(QASearchRow):
    answer_text: str


class QACountRow(TypedDict):
    num_questions: int


class ParagraphSearchRow(TypedDict):
    chapter_number: int
    paragraph_number: int


class ParagraphRow(ParagraphSearchRow):
    chapter_title: str
    text: str


_ACMT = TypeVar('_ACMT')
AsyncIterableContextManager = AsyncContextManager[AsyncIterable[_ACMT]]

_select_confessions = confesses.select() \
    .order_by(confesses.c.command.asc())


def get_confessions() -> AsyncIterableContextManager[ConfessionRow]:
    return pg.query(_select_confessions)


_select_confession = select([confesses.c.id,
                             confesses.c.command,
                             confesses.c.name,
                             confess_types.c.value.label('type')]) \
    .select_from(confesses.join(confess_types))


async def get_confession(command: str) -> ConfessionRow:
    query = _select_confession.where(confesses.c.command == command.lower())
    row = await pg.fetchrow(query)

    if not row:
        return None

    return ConfessionRow(id=row['id'], command=row['command'], name=row['name'],
                         type=ConfessType[row['type']])


_chapters_select = select([confess_chapters.c.chapter_number,
                           confess_chapters.c.chapter_title]) \
    .select_from(confess_chapters.join(confesses)) \
    .order_by(confess_chapters.c.chapter_number.asc())


def get_chapters(confession: ConfessionRow) -> AsyncIterableContextManager[ChapterRow]:
    return pg.query(_chapters_select.where(confesses.c.id == confession['id']))


_paragraph_select = select([confess_chapters.c.chapter_title,
                            confess_paragraphs.c.chapter_number,
                            confess_paragraphs.c.paragraph_number,
                            confess_paragraphs.c.text]) \
    .select_from(confess_paragraphs.join(confesses).join(confess_chapters))


async def get_paragraph(confession: ConfessionRow, chapter: int, paragraph: int) -> ParagraphRow:
    return await pg.fetchrow(_paragraph_select
                             .where(confesses.c.id == confession['id'])
                             .where(confess_chapters.c.chapter_number == chapter)
                             .where(confess_paragraphs.c.chapter_number == chapter)
                             .where(confess_paragraphs.c.paragraph_number == paragraph))


_paragraph_search = select([confess_paragraphs.c.chapter_number,
                            confess_paragraphs.c.paragraph_number]) \
    .select_from(confess_paragraphs.join(confesses)) \
    .order_by(confess_paragraphs.c.chapter_number.asc())


def search_paragraphs(confession: ConfessionRow, terms: Sequence[str]) -> \
        AsyncIterableContextManager[ParagraphSearchRow]:
    return pg.query(_paragraph_search
                    .where(confesses.c.id == confession['id'])
                    .where(func.to_tsvector('english', confess_paragraphs.c.text)
                           .match(' & '.join(terms), postgresql_regconfig='english')))


_questions_select = select([confess_qas.c.question_number,
                            confess_qas.c.question_text]) \
    .select_from(confess_qas.join(confesses)) \
    .order_by(confess_qas.c.question_number.asc())


def get_questions(confession: ConfessionRow) -> AsyncIterableContextManager[QASearchRow]:
    return pg.query(_questions_select.where(confesses.c.id == confession['id']))


_questions_count = select([func.count(confess_qas.c.id).label('num_questions')])


async def get_question_count(confession: ConfessionRow) -> int:
    row = await pg.fetchrow(_questions_count.where(confess_qas.c.confess_id == confession['id']))
    return row['num_questions']


_question_select = select([confess_qas.c.question_number,
                           confess_qas.c.question_text,
                           confess_qas.c.answer_text]) \
    .select_from(confess_qas.join(confesses))


async def get_question(confession: ConfessionRow, question_number: int) -> QARow:
    return await pg.fetchrow(_question_select
                             .where(confesses.c.id == confession['id'])
                             .where(confess_qas.c.question_number == question_number))


_qas_search = select([confess_qas.c.question_number,
                      confess_qas.c.question_text]) \
    .select_from(confess_qas.join(confesses)) \
    .order_by(confess_qas.c.question_number.asc())


def search_qas(confession: ConfessionRow, terms: Sequence[str]) -> \
        AsyncIterableContextManager[QASearchRow]:
    return pg.query(_qas_search
                    .where(confesses.c.id == confession['id'])
                    .where(func.to_tsvector('english',
                                            confess_qas.c.question_text + ' ' + confess_qas.c.answer_text)
                           .match(' & '.join(terms), postgresql_regconfig='english')))

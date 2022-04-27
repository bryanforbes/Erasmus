from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from sqlalchemy import (
    Boolean,
    Column,
    Enum as _SAEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    asc,
    func,
    select,
    text,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship
from sqlalchemy.sql import ColumnElement

from ..exceptions import InvalidConfessionError, NoSectionError, NoSectionsError
from .base import mapper_registry


def _search_columns(
    title_column: Any,
    text_column: Any,
    terms: Sequence[str],
    /,
) -> ColumnElement[Boolean]:
    return func.to_tsvector(
        text("'english'"),
        title_column + text("' '") + text_column,
    ).match(' & '.join(terms), postgresql_regconfig='english')


class ConfessionTypeEnum(Enum):
    ARTICLES = 'ARTICLES'
    CHAPTERS = 'CHAPTERS'
    QA = 'QA'

    def __repr__(self, /) -> str:
        return '<%s.%s>' % (self.__class__.__name__, self.name)


@mapper_registry.mapped
@dataclass
class ConfessionType:
    __tablename__ = 'confession_types'
    __sa_dataclass_metadata_key__ = 'sa'

    id: int = field(init=False, metadata={'sa': Column(Integer, primary_key=True)})
    value: ConfessionTypeEnum = field(
        metadata={
            'sa': Column(_SAEnum(ConfessionTypeEnum), unique=True, nullable=False)
        }
    )


class NumberingTypeEnum(Enum):
    ARABIC = 'ARABIC'
    ROMAN = 'ROMAN'

    def __repr__(self, /) -> str:
        return '<%s.%s>' % (self.__class__.__name__, self.name)


@mapper_registry.mapped
@dataclass
class ConfessionNumberingType:
    __tablename__ = 'confession_numbering_types'
    __sa_dataclass_metadata_key__ = 'sa'

    id: int = field(init=False, metadata={'sa': Column(Integer, primary_key=True)})
    numbering: NumberingTypeEnum = field(
        metadata={'sa': Column(_SAEnum(NumberingTypeEnum), unique=True, nullable=False)}
    )


@mapper_registry.mapped
@dataclass
class Chapter:
    __tablename__ = 'confession_chapters'
    __sa_dataclass_metadata_key__ = 'sa'

    id: int = field(init=False, metadata={'sa': Column(Integer, primary_key=True)})
    confess_id: int = field(
        metadata={'sa': Column(Integer, ForeignKey('confessions.id'), nullable=False)}
    )
    chapter_number: int = field(metadata={'sa': Column(Integer, nullable=False)})
    chapter_title: str = field(metadata={'sa': Column(String, nullable=False)})


@mapper_registry.mapped
@dataclass
class Paragraph:
    __tablename__ = 'confession_paragraphs'
    __sa_dataclass_metadata_key__ = 'sa'

    id: int = field(init=False, metadata={'sa': Column(Integer, primary_key=True)})
    confess_id: int = field(
        metadata={'sa': Column(Integer, ForeignKey('confessions.id'), nullable=False)}
    )
    chapter_number: int = field(metadata={'sa': Column(Integer, nullable=False)})
    paragraph_number: int = field(metadata={'sa': Column(Integer, nullable=False)})
    text: str = field(metadata={'sa': Column(Text, nullable=False)})

    chapter: Chapter = field(
        init=False,
        metadata={
            'sa': relationship(
                'Chapter',
                lazy='joined',
                primaryjoin='and_('
                'Paragraph.chapter_number == foreign(Chapter.chapter_number),'
                'Paragraph.confess_id == foreign(Chapter.confess_id))',
                uselist=False,
            )
        },
    )


@mapper_registry.mapped
@dataclass
class Question:
    __tablename__ = 'confession_questions'
    __sa_dataclass_metadata_key__ = 'sa'

    id: int = field(init=False, metadata={'sa': Column(Integer, primary_key=True)})
    confess_id: int = field(
        metadata={'sa': Column(Integer, ForeignKey('confessions.id'), nullable=False)}
    )
    question_number: int = field(metadata={'sa': Column(Integer, nullable=False)})
    question_text: str = field(metadata={'sa': Column(Text, nullable=False)})
    answer_text: str = field(metadata={'sa': Column(Text, nullable=False)})


@mapper_registry.mapped
@dataclass
class Article:
    __tablename__ = 'confession_articles'
    __sa_dataclass_metadata_key__ = 'sa'

    id: int = field(init=False, metadata={'sa': Column(Integer, primary_key=True)})
    confess_id: int = field(
        metadata={'sa': Column(Integer, ForeignKey('confessions.id'), nullable=False)}
    )
    article_number: int = field(metadata={'sa': Column(Integer, nullable=False)})
    title: str = field(metadata={'sa': Column(Text, nullable=False)})
    text: str = field(metadata={'sa': Column(Text, nullable=False)})


@mapper_registry.mapped
@dataclass
class Confession:
    __tablename__ = 'confessions'
    __sa_dataclass_metadata_key__ = 'sa'

    id: int = field(init=False, metadata={'sa': Column(Integer, primary_key=True)})
    command: str = field(metadata={'sa': Column(String, unique=True, nullable=False)})
    name: str = field(metadata={'sa': Column(String, nullable=False)})
    type_id: int = field(
        metadata={
            'sa': Column(Integer, ForeignKey('confession_types.id'), nullable=False)
        }
    )
    numbering_id: int = field(
        metadata={
            'sa': Column(
                Integer, ForeignKey('confession_numbering_types.id'), nullable=False
            )
        }
    )

    _type: ConfessionType = field(
        metadata={'sa': relationship(ConfessionType, lazy='joined')}
    )
    _numbering: ConfessionNumberingType = field(
        metadata={'sa': relationship(ConfessionNumberingType, lazy='joined')}
    )

    async def get_chapters(self, session: AsyncSession, /) -> AsyncIterator[Chapter]:
        result = await session.stream_scalars(
            select(Chapter)
            .where(Chapter.confess_id == self.id)
            .order_by(asc(Chapter.chapter_number))
        )

        count = 0
        async for chapter in result:
            count += 1
            yield chapter

        if count == 0:
            raise NoSectionsError(self.name, 'chapters')

    async def get_paragraphs(
        self,
        session: AsyncSession,
        /,
    ) -> AsyncIterator[Paragraph]:
        result = await session.stream_scalars(
            select(Paragraph)
            .where(Paragraph.confess_id == self.id)
            .order_by(asc(Paragraph.chapter_number), asc(Paragraph.paragraph_number))
        )

        count = 0
        async for paragraph in result:
            count += 1
            yield paragraph

        if count == 0:
            raise NoSectionsError(self.name, 'paragraphs')

    async def get_paragraph(
        self,
        session: AsyncSession,
        chapter: int,
        paragraph: int,
        /,
    ) -> Paragraph:
        result: Paragraph | None = (
            await session.scalars(
                select(Paragraph)
                .where(Paragraph.confess_id == self.id)
                .where(Paragraph.chapter_number == chapter)
                .where(Paragraph.paragraph_number == paragraph)
            )
        ).first()

        if result is None:
            raise NoSectionError(self.name, f'{chapter}.{paragraph}', 'paragraph')

        return result

    async def search_paragraphs(
        self,
        session: AsyncSession,
        terms: Sequence[str],
        /,
    ) -> AsyncIterator[Paragraph]:
        result = await session.stream_scalars(
            select(Paragraph)
            .join(Chapter, Paragraph.chapter)
            .where(Paragraph.confess_id == self.id)
            .where(_search_columns(Chapter.chapter_title, Paragraph.text, terms))
            .order_by(asc(Paragraph.chapter_number))
        )

        async for paragraph in result:
            yield paragraph

    async def get_questions(self, session: AsyncSession, /) -> AsyncIterator[Question]:
        result = await session.stream_scalars(
            select(Question)
            .where(Question.confess_id == self.id)
            .order_by(asc(Question.question_number))
        )

        async for question in result:
            yield question

    async def get_question_count(self, session: AsyncSession, /) -> int:
        return await session.scalar(
            select([func.count(Question.id)]).where(Question.confess_id == self.id)
        )

    async def get_question(
        self,
        session: AsyncSession,
        question_number: int,
        /,
    ) -> Question:
        question: Question | None = (
            await session.scalars(
                select(Question)
                .where(Question.confess_id == self.id)
                .where(Question.question_number == question_number)
            )
        ).first()

        if question is None:
            raise NoSectionError(self.name, f'{question_number}', 'question')

        return question

    async def search_questions(
        self,
        session: AsyncSession,
        terms: Sequence[str],
        /,
    ) -> AsyncIterator[Question]:
        result = await session.stream_scalars(
            select(Question)
            .where(Question.confess_id == self.id)
            .where(_search_columns(Question.question_text, Question.answer_text, terms))
            .order_by(asc(Question.question_number))
        )

        async for question in result:
            yield question

    async def get_articles(self, session: AsyncSession, /) -> AsyncIterator[Article]:
        result = await session.stream_scalars(
            select(Article)
            .where(Article.confess_id == self.id)
            .order_by(asc(Article.article_number))
        )

        count = 0
        async for article in result:
            count += 1
            yield article

        if count == 0:
            raise NoSectionsError(self.name, 'articles')

    async def get_article(
        self,
        session: AsyncSession,
        article_number: int,
        /,
    ) -> Article:
        article: Article | None = (
            await session.scalars(
                select(Article)
                .where(Article.confess_id == self.id)
                .where(Article.article_number == article_number)
            )
        ).first()

        if article is None:
            raise NoSectionError(self.name, f'{article_number}', 'article')

        return article

    async def search_articles(
        self,
        session: AsyncSession,
        terms: Sequence[str],
        /,
    ) -> AsyncIterator[Article]:
        result = await session.stream_scalars(
            select(Article)
            .where(Article.confess_id == self.id)
            .where(_search_columns(Article.title, Article.text, terms))
            .order_by(asc(Article.article_number))
        )

        async for article in result:
            yield article

    @property
    def type(self, /) -> ConfessionTypeEnum:
        return self._type.value

    @property
    def numbering(self, /) -> NumberingTypeEnum:
        return self._numbering.numbering

    @staticmethod
    async def get_all(session: AsyncSession, /) -> AsyncIterator[Confession]:
        result = await session.stream_scalars(
            select(Confession).order_by(asc(Confession.command))
        )

        async for confession in result:
            yield confession

    @staticmethod
    async def get_by_command(session: AsyncSession, command: str, /) -> Confession:
        c: Confession | None = (
            await session.scalars(
                select(Confession).where(Confession.command == command.lower())
            )
        ).first()

        if c is None:
            raise InvalidConfessionError(command)

        return c

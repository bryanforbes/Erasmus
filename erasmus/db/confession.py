from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from enum import Enum
from typing import cast

from sqlalchemy import Column
from sqlalchemy import Enum as EnumType
from sqlalchemy import ForeignKey, Integer, String, Text, and_, asc, func, select
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager, foreign, joinedload, relationship

from ..exceptions import InvalidConfessionError, NoSectionError, NoSectionsError
from .base import Base


class ConfessionTypeEnum(Enum):
    ARTICLES = 'ARTICLES'
    CHAPTERS = 'CHAPTERS'
    QA = 'QA'

    def __repr__(self, /) -> str:
        return '<%s.%s>' % (self.__class__.__name__, self.name)


class ConfessionType(Base):
    __tablename__ = 'confession_types'

    id: int = Column(Integer, primary_key=True)
    value: ConfessionTypeEnum = Column(
        EnumType(ConfessionTypeEnum), unique=True, nullable=False
    )


class NumberingTypeEnum(Enum):
    ARABIC = 'ARABIC'
    ROMAN = 'ROMAN'

    def __repr__(self, /) -> str:
        return '<%s.%s>' % (self.__class__.__name__, self.name)


class ConfessionNumberingType(Base):
    __tablename__ = 'confession_numbering_types'

    id: int = Column(Integer, primary_key=True)
    numbering: NumberingTypeEnum = Column(
        EnumType(NumberingTypeEnum), unique=True, nullable=False
    )


class Chapter(Base):
    __tablename__ = 'confession_chapters'

    id: int = Column(Integer, primary_key=True)
    confess_id: int = Column(Integer, ForeignKey('confessions.id'), nullable=False)
    chapter_number: int = Column(Integer, nullable=False)
    chapter_title: str = Column(String, nullable=False)


class Paragraph(Base):
    __tablename__ = 'confession_paragraphs'

    id: int = Column(Integer, primary_key=True)
    confess_id: int = Column(Integer, ForeignKey('confessions.id'), nullable=False)
    chapter_number: int = Column(Integer, nullable=False)
    paragraph_number: int = Column(Integer, nullable=False)
    text: str = Column(Text, nullable=False)

    chapter: Chapter = relationship(
        Chapter,
        primaryjoin=lambda: and_(
            Paragraph.chapter_number == foreign(Chapter.chapter_number),
            Paragraph.confess_id == foreign(Chapter.confess_id),
        ),
        uselist=False,
    )


class Question(Base):
    __tablename__ = 'confession_questions'

    id: int = Column(Integer, primary_key=True)
    confess_id: int = Column(Integer, ForeignKey('confessions.id'), nullable=False)
    question_number: int = Column(Integer, nullable=False)
    question_text: str = Column(Text, nullable=False)
    answer_text: str = Column(Text, nullable=False)


class Article(Base):
    __tablename__ = 'confession_articles'

    id: int = Column(Integer, primary_key=True)
    confess_id: int = Column(Integer, ForeignKey('confessions.id'), nullable=False)
    article_number: int = Column(Integer, nullable=False)
    title: str = Column(Text, nullable=False)
    text: str = Column(Text, nullable=False)


class Confession(Base):
    __tablename__ = 'confessions'

    id: int = Column(Integer, primary_key=True)
    command: str = Column(String, unique=True, nullable=False)
    name: str = Column(String, nullable=False)
    type_id: int = Column(Integer, ForeignKey('confession_types.id'), nullable=False)
    numbering_id: int = Column(
        Integer, ForeignKey('confession_numbering_types.id'), nullable=False
    )

    _type: ConfessionType = relationship(ConfessionType, uselist=False)
    _numbering: ConfessionNumberingType = relationship(
        ConfessionNumberingType, uselist=False
    )

    @property
    def type(self) -> ConfessionTypeEnum:
        return self._type.value

    @property
    def numbering(self) -> NumberingTypeEnum:
        return self._numbering.numbering

    async def get_chapters(self, session: AsyncSession, /) -> AsyncIterator[Chapter]:
        count = 0
        chapter_stmt = (
            select(Chapter)
            .where(Chapter.confess_id == self.id)
            .order_by(asc(Chapter.chapter_number))
        )
        results = await session.stream(chapter_stmt)
        async for chapter in results.scalars():
            count += 1
            yield chapter

        if count == 0:
            raise NoSectionsError(self.name, 'chapters')

    async def get_paragraph(
        self,
        session: AsyncSession,
        chapter_number: int,
        paragraph_number: int,
        /,
    ) -> Paragraph:
        stmt = (
            select(Paragraph)
            .outerjoin(Paragraph.chapter)
            .options(contains_eager(Paragraph.chapter))
            .where(Paragraph.confess_id == self.id)
            .where(Paragraph.chapter_number == chapter_number)
            .where(Paragraph.paragraph_number == paragraph_number)
        )
        result = await session.execute(stmt)
        paragraph: Paragraph | None = result.scalars().first()

        if not paragraph:
            raise NoSectionError(
                self.name, f'{chapter_number}.{paragraph_number}', 'paragraph'
            )

        return paragraph

    async def search_paragraphs(
        self,
        session: AsyncSession,
        terms: Sequence[str],
        /,
    ) -> AsyncIterator[Paragraph]:
        stmt = (
            select(Paragraph)
            .outerjoin(Paragraph.chapter)
            .options(contains_eager(Paragraph.chapter))
            .where(Paragraph.confess_id == self.id)
            .where(
                func.to_tsvector(
                    sa_text("'english'"),
                    Chapter.chapter_title + sa_text("' '") + Paragraph.text,
                ).match(' & '.join(terms), postgresql_regconfig='english')
            )
            .order_by(asc(Paragraph.chapter_number))
        )
        results = await session.stream(stmt)
        async for paragraph in results.scalars():
            yield paragraph

    async def get_questions(self, session: AsyncSession, /) -> AsyncIterator[Question]:
        stmt = (
            select(Question)
            .where(Question.confess_id == self.id)
            .order_by(asc(Question.question_number))
        )
        results = await session.stream(stmt)
        async for question in results.scalars():
            yield question

    async def get_question_count(self, session: AsyncSession, /) -> int:
        stmt = select([func.count(Question.id)]).where(Question.confess_id == self.id)
        return cast(int, await session.scalar(stmt))

    async def get_question(
        self,
        session: AsyncSession,
        question_number: int,
        /,
    ) -> Question:
        stmt = (
            select(Question)
            .where(Question.confess_id == self.id)
            .where(Question.question_number == question_number)
        )
        result = await session.execute(stmt)

        question: Question | None = result.scalars().first()

        if not question:
            raise NoSectionError(self.name, f'{question_number}', 'question')

        return question

    async def search_questions(
        self,
        session: AsyncSession,
        terms: Sequence[str],
        /,
    ) -> AsyncIterator[Question]:
        stmt = (
            select(Question)
            .where(Question.confess_id == self.id)
            .where(
                func.to_tsvector(
                    sa_text("'english'"),
                    Question.question_text + sa_text("' '") + Question.answer_text,
                ).match(' & '.join(terms), postgresql_regconfig='english')
            )
            .order_by(asc(Question.question_number))
        )
        results = await session.stream(stmt)
        async for question in results.scalars():
            yield question

    async def get_articles(self, session: AsyncSession, /) -> AsyncIterator[Article]:
        count = 0
        stmt = (
            select(Article)
            .where(Article.confess_id == self.id)
            .order_by(asc(Article.article_number))
        )
        results = await session.stream(stmt)
        async for article in results.scalars():
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
        stmt = (
            select(Article)
            .where(Article.confess_id == self.id)
            .where(Article.article_number == article_number)
        )
        result = await session.execute(stmt)

        article: Article | None = result.scalars().first()

        if not article:
            raise NoSectionError(self.name, f'{article_number}', 'article')

        return article

    async def search_articles(
        self,
        session: AsyncSession,
        terms: Sequence[str],
        /,
    ) -> AsyncIterator[Article]:
        stmt = (
            select(Article)
            .where(Article.confess_id == self.id)
            .where(
                func.to_tsvector(
                    sa_text("'english'"),
                    Article.title + sa_text("' '") + Article.text,
                ).match(' & '.join(terms), postgresql_regconfig='english')
            )
            .order_by(asc(Article.article_number))
        )
        results = await session.stream(stmt)
        async for article in results.scalars():
            yield article

    @staticmethod
    async def get_all(session: AsyncSession) -> AsyncIterator[Confession]:
        stmt = select(Confession).order_by(asc(Confession.command))
        results = await session.stream(stmt)
        async for confession in results.scalars():
            yield confession

    @staticmethod
    async def get_by_command(session: AsyncSession, command: str, /) -> Confession:
        stmt = (
            select(Confession)
            .options(joinedload(Confession._type))
            .options(joinedload(Confession._numbering))
            .where(Confession.command == command.lower())
        )
        result = await session.execute(stmt)

        c: Confession | None = result.scalars().first()

        if not c:
            raise InvalidConfessionError(command)

        return c

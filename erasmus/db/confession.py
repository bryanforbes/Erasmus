from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from more_itertools import peekable
from sqlalchemy import (
    Computed,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    and_,
    func,
    select,
    text as _sa_text,
)
from sqlalchemy.dialects.postgresql import ENUM

from ..exceptions import InvalidConfessionError, NoSectionError, NoSectionsError
from .base import (
    Base,
    Mapped,
    TSVector,
    foreign,
    mapped_column,
    mixin_column,
    model,
    model_mixin,
    relationship,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Sequence

    from botus_receptus.types import Coroutine
    from sqlalchemy.ext.asyncio import AsyncSession


class ConfessionType(Enum):
    ARTICLES = 'ARTICLES'
    CHAPTERS = 'CHAPTERS'
    QA = 'QA'

    def __repr__(self, /) -> str:
        return '<%s.%s>' % (self.__class__.__name__, self.name)


class NumberingType(Enum):
    ARABIC = 'ARABIC'
    ROMAN = 'ROMAN'

    def __repr__(self, /) -> str:
        return '<%s.%s>' % (self.__class__.__name__, self.name)


@model_mixin
class _ConfessionChildMixin(Base):
    confess_id: Mapped[int] = mixin_column(
        lambda: mapped_column(Integer, ForeignKey('confessions.id'), nullable=False)
    )


@model
class Chapter(_ConfessionChildMixin):
    __tablename__ = 'confession_chapters'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chapter_number: Mapped[int] = mapped_column(Integer, nullable=False)
    chapter_title: Mapped[str] = mapped_column(String, nullable=False)


@model
class Paragraph(_ConfessionChildMixin):
    __tablename__ = 'confession_paragraphs'
    __table_args__ = (
        Index(
            'confession_paragraphs_text_idx',
            func.to_tsvector(_sa_text("'english'"), _sa_text("'text'")),
            postgresql_using='gin',
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chapter_number: Mapped[int] = mapped_column(Integer, nullable=False)
    paragraph_number: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    chapter: Mapped[Chapter] = relationship(
        Chapter,
        lazy='joined',
        primaryjoin=lambda: and_(
            Paragraph.chapter_number == foreign(Chapter.chapter_number),
            Paragraph.confess_id == foreign(Chapter.confess_id),
        ),
        uselist=False,
        nullable=False,
    )


@model
class Question(_ConfessionChildMixin):
    __tablename__ = 'confession_questions'
    __table_args__ = (
        Index(
            'confession_questions_search_idx',
            'search_vector',
            postgresql_using='gin',
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question_number: Mapped[int] = mapped_column(Integer, nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    search_vector: Mapped[str] = mapped_column(
        TSVector,
        Computed(
            func.to_tsvector(
                _sa_text("'english'"),
                _sa_text("question_text || ' ' || answer_text"),
            )
        ),
        init=False,
    )


@model
class Article(_ConfessionChildMixin):
    __tablename__ = 'confession_articles'
    __table_args__ = (
        Index(
            'confession_articles_search_idx',
            'search_vector',
            postgresql_using='gin',
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    article_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    search_vector: Mapped[str] = mapped_column(
        TSVector,
        Computed(
            func.to_tsvector(_sa_text("'english'"), _sa_text("title || ' ' || text"))
        ),
        init=False,
    )


@model
class Confession(Base):
    __tablename__ = 'confessions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    command: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[ConfessionType] = mapped_column(
        ENUM(ConfessionType, name='confession_type'), nullable=False
    )
    numbering: Mapped[NumberingType] = mapped_column(
        ENUM(NumberingType, name='confession_numbering_type'), nullable=False
    )
    sortable_name: Mapped[str] = mapped_column(
        String,
        Computed(
            func.regexp_replace(
                _sa_text('name'),
                _sa_text(r"'^(the|an?)\s+(.*)$'"),
                _sa_text(r"'\2, \1'"),
                _sa_text("'i'"),
            )
        ),
        init=False,
    )

    async def get_chapters(self, session: AsyncSession, /) -> AsyncIterator[Chapter]:
        result = peekable(
            await session.scalars(
                select(Chapter)
                .filter(Chapter.confess_id == self.id)
                .order_by(Chapter.chapter_number.asc())
            )
        )

        if result.peek(None) is not None:
            for chapter in result:
                yield chapter
        else:
            raise NoSectionsError(self.name, 'chapters')

    async def get_paragraphs(
        self, session: AsyncSession, /
    ) -> AsyncIterator[Paragraph]:
        result = peekable(
            await session.scalars(
                select(Paragraph)
                .filter(Paragraph.confess_id == self.id)
                .order_by(
                    Paragraph.chapter_number.asc(), Paragraph.paragraph_number.asc()
                )
            )
        )

        if result.peek(None) is not None:
            for paragraph in result:
                yield paragraph
        else:
            raise NoSectionsError(self.name, 'paragraphs')

    async def get_paragraph(
        self, session: AsyncSession, chapter: int, paragraph: int, /
    ) -> Paragraph:
        result: Paragraph | None = (
            await session.scalars(
                select(Paragraph).filter(
                    Paragraph.confess_id == self.id,
                    Paragraph.chapter_number == chapter,
                    Paragraph.paragraph_number == paragraph,
                )
            )
        ).first()

        if result is None:
            raise NoSectionError(self.name, f'{chapter}.{paragraph}', self.type)

        return result

    async def search_paragraphs(
        self, session: AsyncSession, terms: Sequence[str], /
    ) -> AsyncIterator[Paragraph]:
        result = await session.scalars(
            select(Paragraph)
            .join(Chapter, Paragraph.chapter)
            .filter(
                Paragraph.confess_id == self.id,
                func.to_tsvector(
                    _sa_text("'english'"),
                    Chapter.chapter_title + _sa_text("' '") + Paragraph.text,
                ).match(' & '.join(terms), postgresql_regconfig='english'),
            )
            .order_by(Paragraph.chapter_number.asc())
        )

        for paragraph in result:
            yield paragraph

    async def get_questions(self, session: AsyncSession, /) -> AsyncIterator[Question]:
        result = await session.scalars(
            select(Question)
            .filter(Question.confess_id == self.id)
            .order_by(Question.question_number.asc())
        )

        for question in result:
            yield question

    def get_question_count(self, session: AsyncSession, /) -> Coroutine[int]:
        return session.scalar(
            select([func.count(Question.id)]).filter(Question.confess_id == self.id)
        )

    async def get_question(
        self, session: AsyncSession, question_number: int, /
    ) -> Question:
        question: Question | None = (
            await session.scalars(
                select(Question).filter(
                    Question.confess_id == self.id,
                    Question.question_number == question_number,
                )
            )
        ).first()

        if question is None:
            raise NoSectionError(self.name, f'{question_number}', self.type)

        return question

    async def search_questions(
        self, session: AsyncSession, terms: Sequence[str], /
    ) -> AsyncIterator[Question]:
        result = await session.scalars(
            select(Question)
            .filter(
                Question.confess_id == self.id,
                Question.search_vector.match(' & '.join(terms)),
            )
            .order_by(Question.question_number.asc())
        )

        for question in result:
            yield question

    async def get_articles(self, session: AsyncSession, /) -> AsyncIterator[Article]:
        result = peekable(
            await session.scalars(
                select(Article)
                .filter(Article.confess_id == self.id)
                .order_by(Article.article_number.asc())
            )
        )

        if result.peek(None) is not None:
            for article in result:
                yield article
        else:
            raise NoSectionsError(self.name, 'articles')

    async def get_article(
        self, session: AsyncSession, article_number: int, /
    ) -> Article:
        article: Article | None = (
            await session.scalars(
                select(Article).filter(
                    Article.confess_id == self.id,
                    Article.article_number == article_number,
                )
            )
        ).first()

        if article is None:
            raise NoSectionError(self.name, f'{article_number}', self.type)

        return article

    async def search_articles(
        self, session: AsyncSession, terms: Sequence[str], /
    ) -> AsyncIterator[Article]:
        result = await session.scalars(
            select(Article)
            .filter(
                Article.confess_id == self.id,
                Article.search_vector.match(' & '.join(terms)),
            )
            .order_by(Article.article_number.asc())
        )

        for article in result:
            yield article

    @staticmethod
    async def get_all(
        session: AsyncSession, /, order_by_name: bool = False
    ) -> AsyncIterator[Confession]:
        result = await session.scalars(
            select(Confession).order_by(
                Confession.sortable_name.asc()
                if order_by_name
                else Confession.command.asc()
            )
        )

        for confession in result:
            yield confession

    @staticmethod
    async def get_by_command(session: AsyncSession, command: str, /) -> Confession:
        c: Confession | None = (
            await session.scalars(
                select(Confession).filter(Confession.command == command.lower())
            )
        ).first()

        if c is None:
            raise InvalidConfessionError(command)

        return c

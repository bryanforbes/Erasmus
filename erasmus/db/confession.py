from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Column,
    Computed,
    Enum as _SAEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    asc,
    func,
    select,
    text as _sa_text,
)
from sqlalchemy.orm import Mapped, relationship

from ..exceptions import InvalidConfessionError, NoSectionError, NoSectionsError
from .base import TSVector, mapped

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Sequence

    from botus_receptus.types import Coroutine
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.sql import ColumnElement


def _search_columns(
    title_column: Mapped[str], text_column: Mapped[str], terms: Sequence[str], /
) -> ColumnElement[Boolean]:
    return func.to_tsvector(
        _sa_text("'english'"),
        title_column + _sa_text("' '") + text_column,
    ).match(' & '.join(terms), postgresql_regconfig='english')


class ConfessionTypeEnum(Enum):
    ARTICLES = 'ARTICLES'
    CHAPTERS = 'CHAPTERS'
    QA = 'QA'

    def __repr__(self, /) -> str:
        return '<%s.%s>' % (self.__class__.__name__, self.name)


@mapped
@dataclass
class ConfessionType:
    __tablename__ = 'confession_types'
    __sa_dataclass_metadata_key__ = 'sa'

    id: Mapped[int] = field(
        init=False, metadata={'sa': Column(Integer, primary_key=True)}
    )
    value: Mapped[ConfessionTypeEnum] = field(
        metadata={
            'sa': Column(_SAEnum(ConfessionTypeEnum), unique=True, nullable=False)
        }
    )


class NumberingTypeEnum(Enum):
    ARABIC = 'ARABIC'
    ROMAN = 'ROMAN'

    def __repr__(self, /) -> str:
        return '<%s.%s>' % (self.__class__.__name__, self.name)


@mapped
@dataclass
class ConfessionNumberingType:
    __tablename__ = 'confession_numbering_types'
    __sa_dataclass_metadata_key__ = 'sa'

    id: Mapped[int] = field(
        init=False, metadata={'sa': Column(Integer, primary_key=True)}
    )
    numbering: Mapped[NumberingTypeEnum] = field(
        metadata={'sa': Column(_SAEnum(NumberingTypeEnum), unique=True, nullable=False)}
    )


@dataclass
class _ConfessionChildMixin:
    __sa_dataclass_metadata_key__ = 'sa'

    confess_id: Mapped[int] = field(
        metadata={
            'sa': lambda: Column(Integer, ForeignKey('confessions.id'), nullable=False)
        }
    )


@mapped
@dataclass
class Chapter(_ConfessionChildMixin):
    __tablename__ = 'confession_chapters'

    id: Mapped[int] = field(
        init=False, metadata={'sa': Column(Integer, primary_key=True)}
    )
    chapter_number: Mapped[int] = field(
        metadata={'sa': Column(Integer, nullable=False)}
    )
    chapter_title: Mapped[str] = field(metadata={'sa': Column(String, nullable=False)})


@mapped
@dataclass
class Paragraph(_ConfessionChildMixin):
    __tablename__ = 'confession_paragraphs'

    id: Mapped[int] = field(
        init=False, metadata={'sa': Column(Integer, primary_key=True)}
    )
    chapter_number: Mapped[int] = field(
        metadata={'sa': Column(Integer, nullable=False)}
    )
    paragraph_number: Mapped[int] = field(
        metadata={'sa': Column(Integer, nullable=False)}
    )
    text: Mapped[str] = field(metadata={'sa': Column(Text, nullable=False)})

    chapter: Mapped[Chapter] = field(
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

    __table_args__ = (
        Index(
            'confession_paragraphs_text_idx',
            func.to_tsvector(_sa_text("'english'"), _sa_text("'text'")),
            postgresql_using='gin',
        ),
    )


@mapped
@dataclass
class Question(_ConfessionChildMixin):
    __tablename__ = 'confession_questions'

    id: Mapped[int] = field(
        init=False, metadata={'sa': Column(Integer, primary_key=True)}
    )
    question_number: Mapped[int] = field(
        metadata={'sa': Column(Integer, nullable=False)}
    )
    question_text: Mapped[str] = field(metadata={'sa': Column(Text, nullable=False)})
    answer_text: Mapped[str] = field(metadata={'sa': Column(Text, nullable=False)})
    search_vector: Mapped[str] = field(
        metadata={
            'sa': Column(
                TSVector,
                Computed(
                    func.to_tsvector(
                        _sa_text("'english'"),
                        _sa_text("question_text || ' ' || answer_text"),
                    )
                ),
            )
        }
    )

    __table_args__ = (
        Index(
            'confession_questions_search_idx',
            'search_vector',
            postgresql_using='gin',
        ),
    )


@mapped
@dataclass
class Article(_ConfessionChildMixin):
    __tablename__ = 'confession_articles'

    id: Mapped[int] = field(
        init=False, metadata={'sa': Column(Integer, primary_key=True)}
    )
    article_number: Mapped[int] = field(
        metadata={'sa': Column(Integer, nullable=False)}
    )
    title: Mapped[str] = field(metadata={'sa': Column(Text, nullable=False)})
    text: Mapped[str] = field(metadata={'sa': Column(Text, nullable=False)})
    search_vector: Mapped[str] = field(
        metadata={
            'sa': Column(
                TSVector,
                Computed(
                    func.to_tsvector(
                        _sa_text("'english'"), _sa_text("title || ' ' || text")
                    )
                ),
            )
        }
    )

    __table_args__ = (
        Index(
            'confession_articles_search_idx',
            'search_vector',
            postgresql_using='gin',
        ),
    )


@mapped
@dataclass
class Confession:
    __tablename__ = 'confessions'
    __sa_dataclass_metadata_key__ = 'sa'

    id: Mapped[int] = field(
        init=False, metadata={'sa': Column(Integer, primary_key=True)}
    )
    command: Mapped[str] = field(
        metadata={'sa': Column(String, unique=True, nullable=False)}
    )
    name: Mapped[str] = field(metadata={'sa': Column(String, nullable=False)})
    type_id: Mapped[int] = field(
        metadata={
            'sa': Column(Integer, ForeignKey('confession_types.id'), nullable=False)
        }
    )
    numbering_id: Mapped[int] = field(
        metadata={
            'sa': Column(
                Integer, ForeignKey('confession_numbering_types.id'), nullable=False
            )
        }
    )

    _type: Mapped[ConfessionType] = field(
        metadata={'sa': relationship(ConfessionType, lazy='joined')}
    )
    _numbering: Mapped[ConfessionNumberingType] = field(
        metadata={'sa': relationship(ConfessionNumberingType, lazy='joined')}
    )

    sortable_name: Mapped[str] = field(
        init=False,
        metadata={
            'sa': Column(
                String,
                Computed(
                    func.regexp_replace(
                        _sa_text('name'),
                        _sa_text(r"'^(the|an?)\s+(.*)$'"),
                        _sa_text(r"'\2, \1'"),
                        _sa_text("'i'"),
                    )
                ),
            )
        },
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
        self, session: AsyncSession, /
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
        self, session: AsyncSession, chapter: int, paragraph: int, /
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
            raise NoSectionError(self.name, f'{chapter}.{paragraph}', self.type)

        return result

    async def search_paragraphs(
        self, session: AsyncSession, terms: Sequence[str], /
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

    def get_question_count(self, session: AsyncSession, /) -> Coroutine[int]:
        return session.scalar(
            select([func.count(Question.id)]).where(Question.confess_id == self.id)
        )

    async def get_question(
        self, session: AsyncSession, question_number: int, /
    ) -> Question:
        question: Question | None = (
            await session.scalars(
                select(Question)
                .where(Question.confess_id == self.id)
                .where(Question.question_number == question_number)
            )
        ).first()

        if question is None:
            raise NoSectionError(self.name, f'{question_number}', self.type)

        return question

    async def search_questions(
        self, session: AsyncSession, terms: Sequence[str], /
    ) -> AsyncIterator[Question]:
        result = await session.stream_scalars(
            select(Question)
            .where(Question.confess_id == self.id)
            .where(Question.search_vector.match(' & '.join(terms)))
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
        self, session: AsyncSession, article_number: int, /
    ) -> Article:
        article: Article | None = (
            await session.scalars(
                select(Article)
                .where(Article.confess_id == self.id)
                .where(Article.article_number == article_number)
            )
        ).first()

        if article is None:
            raise NoSectionError(self.name, f'{article_number}', self.type)

        return article

    async def search_articles(
        self, session: AsyncSession, terms: Sequence[str], /
    ) -> AsyncIterator[Article]:
        result = await session.stream_scalars(
            select(Article)
            .where(Article.confess_id == self.id)
            .where(Article.search_vector.match(' & '.join(terms)))
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
    async def get_all(
        session: AsyncSession, /, order_by_name: bool = False
    ) -> AsyncIterator[Confession]:
        result = await session.stream_scalars(
            select(Confession).order_by(
                asc(Confession.sortable_name if order_by_name else Confession.command)
            )
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

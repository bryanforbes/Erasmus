from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from enum import Enum
from typing import Any, cast

from ..exceptions import InvalidConfessionError, NoSectionError, NoSectionsError
from .base import Base, db


class ConfessionTypeEnum(Enum):
    ARTICLES = 'ARTICLES'
    CHAPTERS = 'CHAPTERS'
    QA = 'QA'

    def __repr__(self, /) -> str:
        return '<%s.%s>' % (self.__class__.__name__, self.name)


class ConfessionType(Base):
    __tablename__ = 'confession_types'

    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Enum(ConfessionTypeEnum), unique=True, nullable=False)


class NumberingTypeEnum(Enum):
    ARABIC = 'ARABIC'
    ROMAN = 'ROMAN'

    def __repr__(self, /) -> str:
        return '<%s.%s>' % (self.__class__.__name__, self.name)


class ConfessionNumberingType(Base):
    __tablename__ = 'confession_numbering_types'

    id = db.Column(db.Integer, primary_key=True)
    numbering = db.Column(db.Enum(NumberingTypeEnum), unique=True, nullable=False)


class Chapter(Base):
    __tablename__ = 'confession_chapters'

    id = db.Column(db.Integer, primary_key=True)
    confess_id = db.Column(db.Integer, db.ForeignKey('confessions.id'), nullable=False)
    chapter_number = db.Column(db.Integer, nullable=False)
    chapter_title = db.Column(db.String, nullable=False)


class Paragraph(Base):
    chapter: Chapter

    __tablename__ = 'confession_paragraphs'

    id = db.Column(db.Integer, primary_key=True)
    confess_id = db.Column(db.Integer, db.ForeignKey('confessions.id'), nullable=False)
    chapter_number = db.Column(db.Integer, nullable=False)
    paragraph_number = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text, nullable=False)


class Question(Base):
    __tablename__ = 'confession_questions'

    id = db.Column(db.Integer, primary_key=True)
    confess_id = db.Column(db.Integer, db.ForeignKey('confessions.id'), nullable=False)
    question_number = db.Column(db.Integer, nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    answer_text = db.Column(db.Text, nullable=False)


class Article(Base):
    __tablename__ = 'confession_articles'

    id = db.Column(db.Integer, primary_key=True)
    confess_id = db.Column(db.Integer, db.ForeignKey('confessions.id'), nullable=False)
    article_number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.Text, nullable=False)
    text = db.Column(db.Text, nullable=False)


class Confession(Base):
    __tablename__ = 'confessions'

    _type: ConfessionTypeEnum
    _numbering: NumberingTypeEnum

    id = db.Column(db.Integer, primary_key=True)
    command = db.Column(db.String, unique=True, nullable=False)
    name = db.Column(db.String, nullable=False)
    type_id = db.Column(
        db.Integer, db.ForeignKey('confession_types.id'), nullable=False
    )
    numbering_id = db.Column(
        db.Integer, db.ForeignKey('confession_numbering_types.id'), nullable=False
    )

    async def get_chapters(self, /) -> AsyncIterator[Chapter]:
        count = 0
        async with db.transaction():
            async for chapter in Chapter.query.where(
                Chapter.confess_id == self.id  # type: ignore
            ).order_by(db.asc(Chapter.chapter_number)).gino.iterate():
                count += 1
                yield chapter

        if count == 0:
            raise NoSectionsError(self.name, 'chapters')

    async def get_paragraphs(self, /) -> AsyncIterator[Paragraph]:
        loader = Paragraph.load(
            chapter=Chapter.on(
                db.and_(
                    Paragraph.chapter_number == Chapter.chapter_number,  # type: ignore
                    Paragraph.confess_id == Chapter.confess_id,  # type: ignore
                )
            )
        )

        count = 0
        async with db.transaction():
            async for paragraph in (
                loader.query.where(Paragraph.confess_id == self.id)  # type: ignore
                .order_by(
                    db.asc(Paragraph.chapter_number),
                    db.asc(Paragraph.paragraph_number),
                )
                .gino.iterate()
            ):
                count += 1
                yield paragraph

        if count == 0:
            raise NoSectionsError(self.name, 'paragraphs')

    async def get_paragraph(self, chapter: int, paragraph: int, /) -> Paragraph:
        loader = Paragraph.load(
            chapter=Chapter.on(
                db.and_(
                    Paragraph.chapter_number == Chapter.chapter_number,  # type: ignore
                    Paragraph.confess_id == Chapter.confess_id,  # type: ignore
                )
            )
        )

        result = (
            await loader.query.where(Paragraph.confess_id == self.id)  # type: ignore
            .where(Paragraph.chapter_number == chapter)  # type: ignore
            .where(Paragraph.paragraph_number == paragraph)  # type: ignore
            .gino.first()
        )

        if not result:
            raise NoSectionError(self.name, f'{chapter}.{paragraph}', 'paragraph')

        return result

    async def search_paragraphs(
        self,
        terms: Sequence[str],
        /,
    ) -> AsyncIterator[Paragraph]:
        loader = Paragraph.load(
            chapter=Chapter.on(
                db.and_(
                    Paragraph.chapter_number == Chapter.chapter_number,  # type: ignore
                    Paragraph.confess_id == Chapter.confess_id,  # type: ignore
                )
            )
        )
        async with db.transaction():
            async for paragraph in loader.query.where(
                Paragraph.confess_id == self.id  # type: ignore
            ).where(
                db.func.to_tsvector(
                    'english', Chapter.chapter_title + db.text("' '") + Paragraph.text
                ).match(' & '.join(terms))
            ).order_by(
                db.asc(Paragraph.chapter_number)
            ).gino.iterate():
                yield paragraph

    async def get_questions(self, /) -> AsyncIterator[Question]:
        async with db.transaction():
            async for question in Question.query.where(
                Question.confess_id == self.id  # type: ignore
            ).order_by(db.asc(Question.question_number)).gino.iterate():
                yield question

    async def get_question_count(self, /) -> int:
        return cast(
            int,
            await db.scalar(  # type: ignore
                db.select([db.func.count(Question.id)]).where(
                    Question.confess_id == self.id  # type: ignore
                )
            ),
        )

    async def get_question(self, question_number: int, /) -> Question:
        question = (
            await Question.query.where(Question.confess_id == self.id)  # type: ignore
            .where(Question.question_number == question_number)  # type: ignore
            .gino.first()
        )

        if not question:
            raise NoSectionError(self.name, f'{question_number}', 'question')

        return question

    async def search_questions(
        self,
        terms: Sequence[str],
        /,
    ) -> AsyncIterator[Question]:
        async with db.transaction():
            async for question in Question.query.where(
                Question.confess_id == self.id  # type: ignore
            ).where(
                db.func.to_tsvector(
                    'english',
                    Question.question_text + db.text("' '") + Question.answer_text,
                ).match(' & '.join(terms))
            ).order_by(
                db.asc(Question.question_number)
            ).gino.iterate():
                yield question

    async def get_articles(self, /) -> AsyncIterator[Article]:
        count = 0
        async with db.transaction():
            async for article in Article.query.where(
                Article.confess_id == self.id  # type: ignore
            ).order_by(db.asc(Article.article_number)).gino.iterate():
                count += 1
                yield article

        if count == 0:
            raise NoSectionsError(self.name, 'articles')

    async def get_article(self, article_number: int, /) -> Article:
        article = (
            await Article.query.where(Article.confess_id == self.id)  # type: ignore
            .where(Article.article_number == article_number)  # type: ignore
            .gino.first()
        )

        if not article:
            raise NoSectionError(self.name, f'{article_number}', 'article')

        return article

    async def search_articles(self, terms: Sequence[str], /) -> AsyncIterator[Article]:
        async with db.transaction():
            async for article in Article.query.where(
                Article.confess_id == self.id  # type: ignore
            ).where(
                db.func.to_tsvector(
                    'english', Article.title + db.text("' '") + Article.text
                ).match(' & '.join(terms))
            ).order_by(
                db.asc(Article.article_number)
            ).gino.iterate():
                yield article

    @property
    def type(self, /) -> ConfessionTypeEnum:
        return self._type

    @type.setter
    def type(self, value: ConfessionType, /) -> None:
        self._type = cast(Any, value.value)

    @property
    def numbering(self, /) -> NumberingTypeEnum:
        return self._numbering

    @numbering.setter
    def numbering(self, value: ConfessionNumberingType, /) -> None:
        self._numbering = cast(Any, value.numbering)

    @staticmethod
    async def get_all() -> AsyncIterator[Confession]:
        async with db.transaction():
            async for confession in Confession.load(
                type=ConfessionType, numbering=ConfessionNumberingType
            ).query.order_by(db.asc(Confession.command)).gino.iterate():
                yield confession

    @staticmethod
    async def get_by_command(command: str, /) -> Confession:
        c = (
            await Confession.load(
                type=ConfessionType, numbering=ConfessionNumberingType
            )
            .query.where(Confession.command == command.lower())  # type: ignore
            .gino.first()
        )

        if not c:
            raise InvalidConfessionError(command)

        return c

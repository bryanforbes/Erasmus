from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    Computed,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    select,
    text as _sa_text,
)
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import selectinload

from ..exceptions import InvalidConfessionError, NoSectionError
from .base import (
    Base,
    Mapped,
    TSVector,
    deref_column,
    mapped_column,
    model,
    relationship,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Sequence

    from sqlalchemy.ext.asyncio import AsyncSession


class ConfessionType(Enum):
    ARTICLES = 'ARTICLES'
    CHAPTERS = 'CHAPTERS'
    QA = 'QA'
    SECTIONS = 'SECTIONS'

    def __repr__(self, /) -> str:
        return '<%s.%s>' % (self.__class__.__name__, self.name)


class NumberingType(Enum):
    ARABIC = 'ARABIC'
    ROMAN = 'ROMAN'
    ALPHA = 'ALPHA'

    def __repr__(self, /) -> str:
        return '<%s.%s>' % (self.__class__.__name__, self.name)


@model
class Section(Base):
    __tablename__ = 'confession_sections'
    __table_args__ = (
        Index(
            'confession_sections_search_idx',
            'search_vector',
            postgresql_using='gin',
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    confession_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('confessions.id'), nullable=False
    )
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    subsection_number: Mapped[int | None] = mapped_column(Integer)
    title: Mapped[str | None] = mapped_column(Text)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    search_vector: Mapped[str] = mapped_column(
        TSVector,
        Computed(
            func.to_tsvector(
                _sa_text("'english'"),
                func.trim(
                    func.coalesce(deref_column(title), _sa_text("''"))
                    + _sa_text("' '")
                    + deref_column(text),
                    _sa_text("' '"),
                ),
            ),
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
    _subsection_numbering: Mapped[NumberingType | None] = mapped_column(
        ENUM(NumberingType, name='confession_numbering_type'),
        name='subsection_numbering',
        nullable=True,
    )
    sortable_name: Mapped[str] = mapped_column(
        String,
        Computed(
            func.regexp_replace(
                deref_column(name),
                _sa_text(r"'^(the|an?)\s+(.*)$'"),
                _sa_text(r"'\2, \1'"),
                _sa_text("'i'"),
            )
        ),
        init=False,
    )
    sections: Mapped[list[Section]] = relationship(
        Section,
        order_by=lambda: [
            Section.number.asc(),
            Section.subsection_number.asc().nulls_first(),
        ],
        lazy='raise',
    )

    @property
    def subsection_numbering(self) -> NumberingType:
        return self._subsection_numbering or self.numbering

    async def search(
        self, session: AsyncSession, terms: Sequence[str], /
    ) -> list[Section]:
        result = await session.scalars(
            select(Section)
            .filter(
                Section.confession_id == self.id,
                Section.search_vector.match(' & '.join(terms)),
            )
            .order_by(
                Section.number.asc(), Section.subsection_number.asc().nulls_first()
            )
        )

        return list(result)

    async def get_section(
        self,
        session: AsyncSession,
        number: int,
        subsection_number: int | None = None,
        /,
    ) -> Section:
        stmt = select(Section).filter(
            Section.confession_id == self.id,
            Section.number == number,
        )

        if subsection_number is not None:
            stmt = stmt.filter(Section.subsection_number == subsection_number)

        result: Section | None = (await session.scalars(stmt)).first()

        if result is None:
            formatted_number = f'{number}'

            if subsection_number is not None:
                formatted_number = f'{formatted_number}.{subsection_number}'

            raise NoSectionError(self.name, formatted_number, self.type)

        return result

    @staticmethod
    async def get_all(
        session: AsyncSession,
        /,
        order_by_name: bool = False,
        load_sections: bool = False,
    ) -> AsyncIterator[Confession]:
        stmt = select(Confession).order_by(
            Confession.sortable_name.asc()
            if order_by_name
            else Confession.command.asc()
        )

        if load_sections:
            stmt = stmt.options(selectinload(Confession.sections))

        result = await session.scalars(stmt)

        for confession in result:
            yield confession

    @staticmethod
    async def get_by_command(
        session: AsyncSession, command: str, /, load_sections: bool = False
    ) -> Confession:
        stmt = select(Confession).filter(Confession.command == command.lower())

        if load_sections:
            stmt = stmt.options(selectinload(Confession.sections))

        c: Confession | None = (await session.scalars(stmt)).first()

        if c is None:
            raise InvalidConfessionError(command)

        return c

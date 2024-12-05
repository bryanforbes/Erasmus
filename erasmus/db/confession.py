from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    Computed,
    ForeignKey,
    Function,
    Index,
    SQLColumnExpression,
    Text as _sa_Text,
    cast,
    func,
    select,
    text as _sa_text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, selectinload

from ..exceptions import InvalidConfessionError, NoSectionError
from .base import Base, Text, TSVector
from .enums import ConfessionType, NumberingType  # noqa: TC001

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from sqlalchemy.ext.asyncio import AsyncSession


def _remove_markdown_links(column: SQLColumnExpression[str]) -> Function[str]:
    return func.regexp_replace(
        column,
        _sa_text(r"'\[(.*?)\]\(.*?\)'"),
        _sa_text(r"'\1'"),
        _sa_text("'g'"),
    )


class Section(Base):
    __tablename__ = 'confession_sections'

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    confession_id: Mapped[int] = mapped_column(ForeignKey('confessions.id'))
    number: Mapped[int]
    subsection_number: Mapped[int | None]
    title: Mapped[Text | None] = mapped_column()
    text: Mapped[Text] = mapped_column()
    text_stripped: Mapped[Text] = mapped_column(
        Computed(_remove_markdown_links(text)),
        init=False,
    )
    search_vector: Mapped[TSVector] = mapped_column(
        Computed(
            func.to_tsvector(
                _sa_text("'english'"),
                func.trim(
                    cast(func.coalesce(title, _sa_text("''")), _sa_Text)
                    + _sa_text("' '")
                    + cast(
                        _remove_markdown_links(text),
                        _sa_Text,
                    ),
                    _sa_text("' '"),
                ),
            ),
        ),
        init=False,
    )

    __table_args__ = (
        Index(
            'confession_sections_search_idx',
            search_vector,
            postgresql_using='gin',
        ),
    )


class Confession(Base):
    __tablename__ = 'confessions'

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    command: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str] = mapped_column()
    type: Mapped[ConfessionType]
    numbering: Mapped[NumberingType]
    _subsection_numbering: Mapped[NumberingType | None] = mapped_column(
        name='subsection_numbering',
    )
    sortable_name: Mapped[str] = mapped_column(
        Computed(
            func.regexp_replace(
                name,
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
        init=False,
    )

    @property
    def subsection_numbering(self) -> NumberingType:
        return self._subsection_numbering or self.numbering

    async def search(self, session: AsyncSession, terms: str, /) -> list[Section]:
        tsquery = func.plainto_tsquery(_sa_text("'english'"), terms)
        section_query = (
            select(Section)
            .where(Section.confession_id == self.id)
            .where(Section.search_vector.bool_op('@@')(tsquery))
            .order_by(
                Section.number.asc(), Section.subsection_number.asc().nulls_first()
            )
            .subquery()
        )

        headline_query = select(
            section_query.c.id,
            section_query.c.confession_id,
            section_query.c.number,
            section_query.c.subsection_number,
            section_query.c.text,
            func.ts_headline(
                _sa_text("'english'"),
                section_query.c.title,
                tsquery,
                _sa_text("'HighlightAll=true, StartSel=*, StopSel=*'"),
            ).label('title'),
            func.ts_headline(
                _sa_text("'english'"),
                section_query.c.text_stripped,
                tsquery,
                _sa_text("'StartSel=**, StopSel=**'"),
            ).label('text_stripped'),
            section_query.c.search_vector,
        )

        result = await session.scalars(select(Section).from_statement(headline_query))

        return list(result)

    async def get_section(
        self,
        session: AsyncSession,
        number: int,
        subsection_number: int | None = None,
        /,
    ) -> Section:
        stmt = (
            select(Section)
            .where(Section.confession_id == self.id)
            .where(Section.number == number)
        )

        if subsection_number is not None:
            stmt = stmt.where(Section.subsection_number == subsection_number)

        result: Section | None = (await session.scalars(stmt.limit(1))).first()

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
        *,
        order_by_name: bool = False,
        load_sections: bool = False,
    ) -> AsyncIterator[Confession]:
        stmt = select(Confession)

        if order_by_name:
            stmt = stmt.order_by(Confession.sortable_name.asc())
        else:
            stmt = stmt.order_by(Confession.command.asc())

        if load_sections:
            stmt = stmt.options(selectinload(Confession.sections))

        result = await session.scalars(stmt)

        for confession in result:
            yield confession

    @staticmethod
    async def get_by_command(
        session: AsyncSession, command: str, /, *, load_sections: bool = False
    ) -> Confession:
        stmt = select(Confession).where(Confession.command == command.lower())

        if load_sections:
            stmt = stmt.options(selectinload(Confession.sections))

        c: Confession | None = (await session.scalars(stmt.limit(1))).first()

        if c is None:
            raise InvalidConfessionError(command)

        return c

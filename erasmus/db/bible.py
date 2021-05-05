from __future__ import annotations

from collections.abc import AsyncIterator
from typing import TypeVar, cast

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    asc,
    select,
)
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import (
    Mapped,
    declarative_mixin,
    declared_attr,
    joinedload,
    relationship,
)

from ..exceptions import InvalidVersionError
from ..protocols import Bible
from .base import Base, Snowflake

T = TypeVar('T')


class BibleVersion(Base):
    __tablename__ = 'bible_versions'

    id: int = Column(Integer, primary_key=True)
    command: str = Column(String, unique=True, nullable=False)
    name: str = Column(String, nullable=False)
    abbr: str = Column(String, nullable=False)
    service: str = Column(String, nullable=False)
    service_version: str = Column(String, nullable=False)
    rtl = Column(Boolean)
    books: int = Column(BigInteger, nullable=False)

    def as_bible(self, /) -> Bible:
        return cast(Bible, self)

    async def set_for_user(self, session: AsyncSession, user_id: int, /) -> None:
        await session.execute(
            insert(UserPref)
            .values(user_id=user_id, bible_id=self.id)
            .on_conflict_do_update(index_elements=['user_id'], set_=('bible_id',))
        )

    async def set_for_guild(self, session: AsyncSession, guild_id: int, /) -> None:
        await session.execute(
            insert(GuildPref)
            .values(guild_id=guild_id, bible_id=self.id)
            .on_conflict_do_update(index_elements=['guild_id'], set_=('bible_id',))
        )

    @staticmethod
    async def get_all(
        session: AsyncSession, /, *, ordered: bool = False
    ) -> AsyncIterator[BibleVersion]:
        stmt = select(BibleVersion)

        if ordered:
            stmt = stmt.order_by(asc(BibleVersion.command))

        result = await session.execute(stmt)
        for version in result.scalars().all():
            yield version

    @staticmethod
    async def get_by_command(session: AsyncSession, command: str, /) -> BibleVersion:
        stmt = select(BibleVersion).where(BibleVersion.command == command)
        result = await session.execute(stmt)
        bible: BibleVersion | None = result.scalars().first()

        if not bible:
            raise InvalidVersionError(command)

        return bible

    @staticmethod
    async def get_by_abbr(session: AsyncSession, abbr: str, /) -> BibleVersion | None:
        stmt = select(BibleVersion).where(BibleVersion.command.ilike(abbr))
        result = await session.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def get_for_user(
        session: AsyncSession,
        user_id: int,
        guild_id: int | None,
        /,
    ) -> BibleVersion:
        user_pref: UserPref | None = await session.get(
            UserPref, user_id, options=[joinedload(UserPref.bible_version)]
        )

        if user_pref is not None and user_pref.bible_version is not None:
            return user_pref.bible_version

        if guild_id is not None:
            guild_pref: GuildPref | None = await session.get(
                GuildPref, guild_id, options=[joinedload(GuildPref.bible_version)]
            )

            if guild_pref is not None and guild_pref.bible_version is not None:
                return guild_pref.bible_version

        return await BibleVersion.get_by_command(session, 'esv')


@declarative_mixin
class PrefMixin:
    @declared_attr
    def bible_id(self) -> Mapped[int]:
        return Column(Integer, ForeignKey('bible_versions.id'))

    @declared_attr
    def bible_version(self) -> Mapped[BibleVersion | None]:
        return relationship(BibleVersion, uselist=False)

    @classmethod
    async def get(cls: type[T], session: AsyncSession, id: int, /) -> T | None:
        return cast('T | None', await session.get(cls, id))


class UserPref(PrefMixin, Base):
    __tablename__ = 'user_prefs'

    user_id: int = Column(Snowflake, primary_key=True)


class GuildPref(PrefMixin, Base):
    __tablename__ = 'guild_prefs'

    guild_id: int = Column(Snowflake, primary_key=True)

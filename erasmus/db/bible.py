from __future__ import annotations

from typing import TYPE_CHECKING

import pendulum
from botus_receptus.sqlalchemy import Flag, Snowflake
from sqlalchemy import (
    Boolean,
    Computed,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
    select,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, insert

from ..data import SectionFlag
from ..exceptions import InvalidVersionError
from .base import (
    Base,
    Mapped,
    deref_column,
    foreign,
    mapped_column,
    mixin_column,
    model,
    model_mixin,
    relationship,
)
from .types import DateTime, Time, Timezone

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    import discord
    from botus_receptus.types import Coroutine
    from pendulum.tz.timezone import Timezone as _Timezone
    from sqlalchemy.ext.asyncio import AsyncSession


@model
class BibleVersion(Base):
    __tablename__ = 'bible_versions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    command: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    abbr: Mapped[str] = mapped_column(String, nullable=False)
    service: Mapped[str] = mapped_column(String, nullable=False)
    service_version: Mapped[str] = mapped_column(String, nullable=False)
    rtl: Mapped[bool | None] = mapped_column(Boolean)
    books: Mapped[SectionFlag] = mapped_column(Flag(SectionFlag), nullable=False)
    book_mapping: Mapped[dict[str, str] | None] = mapped_column(
        JSONB(none_as_null=True)
    )
    sortable_name: Mapped[str] = mapped_column(
        String,
        Computed(
            func.regexp_replace(
                deref_column(name),
                text(r"'^(the|an?)\s+(.*)$'"),
                text(r"'\2, \1'"),
                text("'i'"),
            )
        ),
        init=False,
    )

    __table_args__ = (
        Index(
            'bible_versions_sortable_name_order_idx',
            deref_column(sortable_name).asc(),
        ),
    )

    async def set_for_user(
        self, session: AsyncSession, user: discord.User | discord.Member, /
    ) -> None:
        await session.execute(
            insert(UserPref)
            .values(user_id=user.id, bible_id=self.id)
            .on_conflict_do_update(
                index_elements=['user_id'], set_={'bible_id': self.id}
            )
        )

    async def set_for_guild(
        self, session: AsyncSession, guild: discord.Guild, /
    ) -> None:
        await session.execute(
            insert(GuildPref)
            .values(guild_id=guild.id, bible_id=self.id)
            .on_conflict_do_update(
                index_elements=['guild_id'], set_={'bible_id': self.id}
            )
        )

    @staticmethod
    def create(
        *,
        command: str,
        name: str,
        abbr: str,
        service: str,
        service_version: str,
        books: str,
        rtl: bool,
        book_mapping: dict[str, str] | None,
    ) -> BibleVersion:
        return BibleVersion(
            command=command,
            name=name,
            abbr=abbr,
            service=service,
            service_version=service_version,
            rtl=rtl,
            books=SectionFlag.from_book_names(books),
            book_mapping=book_mapping,
        )

    @staticmethod
    async def get_all(
        session: AsyncSession,
        /,
        *,
        ordered: bool = False,
        search_term: str | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[BibleVersion]:
        stmt = select(BibleVersion)

        if ordered:
            stmt = stmt.order_by(BibleVersion.sortable_name.asc())

        if limit:
            stmt = stmt.limit(limit)

        if search_term is not None:
            search_term = search_term.lower()
            stmt = stmt.filter(
                func.lower(BibleVersion.command).startswith(
                    search_term, autoescape=True
                )
                | func.lower(BibleVersion.abbr).startswith(search_term, autoescape=True)
                | func.lower(BibleVersion.name).contains(search_term, autoescape=True)
            )

        result = await session.scalars(stmt)

        for version in result:
            yield version

    @staticmethod
    async def get_by_command(session: AsyncSession, command: str, /) -> BibleVersion:
        bible: BibleVersion | None = (
            await session.scalars(
                select(BibleVersion).filter(BibleVersion.command == command)
            )
        ).first()

        if bible is None:
            raise InvalidVersionError(command)

        return bible

    @staticmethod
    async def get_by_abbr(session: AsyncSession, abbr: str, /) -> BibleVersion | None:
        return (
            await session.scalars(
                select(BibleVersion).filter(BibleVersion.command.ilike(abbr))
            )
        ).first()

    @staticmethod
    async def get_for(
        session: AsyncSession,
        /,
        *,
        user: discord.User | discord.Member | discord.Object | None = None,
        guild: discord.Guild | discord.Object | None = None,
    ) -> BibleVersion:
        if user is not None:
            user_pref = await session.get(UserPref, user.id)

            if user_pref is not None and user_pref.bible_version is not None:
                return user_pref.bible_version

        if guild is not None:
            guild_pref = await session.get(GuildPref, guild.id)

            if guild_pref is not None and guild_pref.bible_version is not None:
                return guild_pref.bible_version

        return await BibleVersion.get_by_command(session, 'esv')


@model_mixin
class _BibleVersionMixin(Base):
    bible_id: Mapped[int | None] = mixin_column(
        lambda: mapped_column(Integer, ForeignKey('bible_versions.id'))
    )
    bible_version: Mapped[BibleVersion | None] = relationship(
        BibleVersion, lazy='joined', uselist=False
    )


@model
class UserPref(_BibleVersionMixin):
    __tablename__ = 'user_prefs'

    user_id: Mapped[int] = mapped_column(Snowflake, primary_key=True, init=True)

    @staticmethod
    def for_user(
        session: AsyncSession, user: discord.User | discord.Member, /
    ) -> Coroutine[UserPref | None]:
        return session.get(UserPref, user.id)


@model
class GuildPref(_BibleVersionMixin):
    __tablename__ = 'guild_prefs'

    guild_id: Mapped[int] = mapped_column(Snowflake, primary_key=True, init=True)

    @staticmethod
    def for_guild(
        session: AsyncSession, guild: discord.Guild, /
    ) -> Coroutine[GuildPref | None]:
        return session.get(GuildPref, guild.id)


@model
class DailyBread(Base):
    __tablename__ = 'daily_breads'

    guild_id: Mapped[int] = mapped_column(Snowflake, primary_key=True, init=True)
    channel_id: Mapped[int] = mapped_column(Snowflake, nullable=False)
    thread_id: Mapped[int | None] = mapped_column(Snowflake)
    url: Mapped[str] = mapped_column(String, nullable=False)
    next_scheduled: Mapped[pendulum.DateTime] = mapped_column(
        DateTime(timezone=False), nullable=False
    )
    time: Mapped[pendulum.Time] = mapped_column(Time, nullable=False)
    timezone: Mapped[_Timezone] = mapped_column(Timezone, nullable=False)

    prefs: Mapped[GuildPref | None] = relationship(
        GuildPref,
        lazy='joined',
        uselist=False,
        viewonly=True,
        primaryjoin=deref_column(guild_id) == foreign(GuildPref.guild_id),
    )

    @staticmethod
    def for_guild(
        session: AsyncSession, guild: discord.Guild, /
    ) -> Coroutine[DailyBread | None]:
        return session.get(DailyBread, guild.id)

    @staticmethod
    async def scheduled(session: AsyncSession, /) -> list[DailyBread]:
        return (
            await session.scalars(
                select(DailyBread).filter(
                    DailyBread.next_scheduled
                    <= pendulum.now(pendulum.UTC).set(second=0, microsecond=0)
                )
            )
        ).fetchall()

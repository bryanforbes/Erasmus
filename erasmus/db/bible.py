from __future__ import annotations

from collections.abc import AsyncIterator
from typing import cast

from botus_receptus.gino import Snowflake

from ..exceptions import InvalidVersionError
from ..protocols import Bible
from .base import Base, db


class BibleVersion(Base):
    __tablename__ = 'bible_versions'

    id = db.Column(db.Integer, primary_key=True)
    command = db.Column(db.String, unique=True, nullable=False)
    name = db.Column(db.String, nullable=False)
    abbr = db.Column(db.String, nullable=False)
    service = db.Column(db.String, nullable=False)
    service_version = db.Column(db.String, nullable=False)
    rtl = db.Column(db.Boolean)
    books = db.Column(db.BigInteger, nullable=False)

    def as_bible(self) -> Bible:
        return cast(Bible, self)

    async def set_for_user(self, user_id: int) -> None:
        await UserPref.create_or_update(
            set_=('bible_id',), user_id=user_id, bible_id=self.id
        )

    async def set_for_guild(self, guild_id: int) -> None:
        await GuildPref.create_or_update(
            set_=('bible_id',), guild_id=guild_id, bible_id=self.id
        )

    @staticmethod
    async def get_all(*, ordered: bool = False) -> AsyncIterator[BibleVersion]:
        query = BibleVersion.query

        if ordered:
            query = query.order_by(db.asc(BibleVersion.command))

        async with db.transaction():
            async for version in query.gino.iterate():
                yield version

    @staticmethod
    async def get_by_command(command: str) -> BibleVersion:
        bible = await BibleVersion.query.where(
            BibleVersion.command == command
        ).gino.first()

        if not bible:
            raise InvalidVersionError(command)

        return bible

    @staticmethod
    async def get_by_abbr(abbr: str) -> BibleVersion | None:
        return await BibleVersion.query.where(
            BibleVersion.command.ilike(abbr)
        ).gino.first()

    @staticmethod
    async def get_for_user(user_id: int, guild_id: int | None) -> BibleVersion:
        user_pref = (
            await UserPref.load(bible_version=BibleVersion)
            .query.where(UserPref.user_id == user_id)
            .gino.first()
        )

        if user_pref is not None and user_pref.bible_version is not None:
            return user_pref.bible_version

        if guild_id is not None:
            guild_pref = (
                await GuildPref.load(bible_version=BibleVersion)
                .query.where(GuildPref.guild_id == guild_id)
                .gino.first()
            )

            if guild_pref is not None and guild_pref.bible_version is not None:
                return guild_pref.bible_version

        return await BibleVersion.get_by_command('esv')


class UserPref(Base):
    __tablename__ = 'user_prefs'

    bible_version: BibleVersion | None

    user_id = db.Column(Snowflake, primary_key=True)
    bible_id = db.Column(db.Integer, db.ForeignKey('bible_versions.id'))


class GuildPref(Base):
    __tablename__ = 'guild_prefs'

    bible_version: BibleVersion | None

    guild_id = db.Column(Snowflake, primary_key=True)
    bible_id = db.Column(db.Integer, db.ForeignKey('bible_versions.id'))

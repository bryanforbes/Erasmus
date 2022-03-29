from __future__ import annotations

from collections.abc import AsyncIterator
from typing import cast

import discord
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

    def as_bible(self, /) -> Bible:
        return cast(Bible, self)

    async def set_for_user(self, user: discord.User | discord.Member, /) -> None:
        await UserPref.create_or_update(
            set_=('bible_id',), user_id=user.id, bible_id=self.id
        )

    async def set_for_guild(self, guild: discord.Guild, /) -> None:
        await GuildPref.create_or_update(
            set_=('bible_id',), guild_id=guild.id, bible_id=self.id
        )

    @staticmethod
    async def get_all(
        *, ordered: bool = False, search_term: str | None = None
    ) -> AsyncIterator[BibleVersion]:
        query = BibleVersion.query

        if ordered:
            query = query.order_by(db.asc(BibleVersion.command))

        if search_term is not None:
            search_term = search_term.lower()
            query = query.where(
                db.or_(
                    db.func.lower(BibleVersion.command).startswith(
                        search_term, autoescape=True
                    ),
                    db.func.lower(BibleVersion.abbr).startswith(
                        search_term, autoescape=True
                    ),
                    db.func.lower(BibleVersion.name).contains(
                        search_term, autoescape=True
                    ),
                )
            )

        async with db.transaction():
            async for version in query.gino.iterate():
                yield version

    @staticmethod
    async def get_by_command(command: str, /) -> BibleVersion:
        bible = await BibleVersion.query.where(
            BibleVersion.command == command  # type: ignore
        ).gino.first()

        if not bible:
            raise InvalidVersionError(command)

        return bible

    @staticmethod
    async def get_by_abbr(abbr: str, /) -> BibleVersion | None:
        return await BibleVersion.query.where(
            BibleVersion.command.ilike(abbr)  # type: ignore
        ).gino.first()

    @staticmethod
    async def get_for_user(
        user: discord.User | discord.Member,
        guild: discord.Guild | None,
        /,
    ) -> BibleVersion:
        user_pref = (
            await UserPref.load(bible_version=BibleVersion)
            .query.where(UserPref.user_id == user.id)  # type: ignore
            .gino.first()
        )

        if user_pref is not None and user_pref.bible_version is not None:
            return user_pref.bible_version

        if guild is not None:
            guild_pref = (
                await GuildPref.load(bible_version=BibleVersion)
                .query.where(GuildPref.guild_id == guild.id)  # type: ignore
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

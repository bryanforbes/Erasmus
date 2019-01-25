from __future__ import annotations

from typing import Optional, AsyncIterator
from botus_receptus.gino import db, Base, Snowflake, create_or_update

from ..exceptions import InvalidVersionError


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

    async def set_for_user(self, user_id: int) -> None:
        await create_or_update(
            UserPref, set_=('bible_id',), user_id=user_id, bible_id=self.id
        )

    @staticmethod
    async def get_all(
        *, ordered: bool = False
    ) -> AsyncIterator[BibleVersion]:  # noqa: F821
        query = BibleVersion.query

        if ordered:
            query = query.order_by(db.asc(BibleVersion.command))

        async with db.transaction():
            async for version in query.gino.iterate():
                yield version

    @staticmethod
    async def get_by_command(command: str) -> BibleVersion:  # noqa: F821
        bible = await BibleVersion.query.where(
            BibleVersion.command == command
        ).gino.first()

        if not bible:
            raise InvalidVersionError(command)

        return bible

    @staticmethod
    async def get_by_abbr(abbr: str) -> Optional[BibleVersion]:  # noqa: F821
        return await BibleVersion.query.where(
            BibleVersion.command.ilike(abbr)
        ).gino.first()

    @staticmethod
    async def get_for_user(user_id: int) -> BibleVersion:  # noqa: F821
        user_pref = (
            await UserPref.load(bible_version=BibleVersion)
            .query.where(UserPref.user_id == user_id)
            .gino.first()
        )

        if user_pref is None or user_pref.bible_version is None:
            return await BibleVersion.get_by_command('esv')

        return user_pref.bible_version


class UserPref(Base):
    bible_version: Optional[BibleVersion]

    __tablename__ = 'user_prefs'

    user_id = db.Column(Snowflake, primary_key=True)
    bible_id = db.Column(db.Integer, db.ForeignKey('bible_versions.id'))

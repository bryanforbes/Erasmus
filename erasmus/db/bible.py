from typing import Optional
from mypy_extensions import TypedDict
from asyncpgsa import pg  # type: ignore
from sqlalchemy.dialects.postgresql import insert  # type: ignore
from .tables import bible_versions, user_prefs
from .types import AIContextManager

__all__ = (
    'Bible', 'get_bibles', 'get_bible', 'get_user_bible', 'set_user_bible',
    'add_bible', 'delete_bible'
)


class Bible(TypedDict):
    id: int
    command: str
    name: str
    abbr: str
    service: str
    service_version: str
    rtl: bool
    books: int


_bible_select = bible_versions.select()
_bible_ordered_select = _bible_select.order_by(bible_versions.c.command.asc())


def get_bibles(*, ordered: bool = False) -> AIContextManager[Bible]:
    return pg.query(_bible_select if not ordered else _bible_ordered_select)


async def get_bible(command: str) -> Optional[Bible]:
    bible = await pg.fetchrow(bible_versions.select()
                              .where(bible_versions.c.command == command))
    if not bible:
        return None

    return bible


_user_bible_select = bible_versions.select() \
    .select_from(bible_versions.join(user_prefs))


async def get_user_bible(user_id: int) -> Optional[Bible]:
    return await pg.fetchrow(_user_bible_select.where(user_prefs.c.user_id == user_id))


async def set_user_bible(user_id: int, bible: Bible) -> None:
    await pg.execute(insert(user_prefs)
                     .values(user_id=user_id,
                             bible_id=bible['id'])
                     .on_conflict_do_update(index_elements=[user_prefs.c.user_id],
                                            set_=dict(bible_id=bible['id'])))


_bible_versions_insert = bible_versions.insert()


async def add_bible(*, command: str, name: str, abbr: str, service: str,
                    service_version: str, rtl: bool = False) -> None:
    await pg.execute(_bible_versions_insert.values(command=command,
                                                   name=name,
                                                   abbr=abbr,
                                                   service=service,
                                                   service_version=service_version,
                                                   rtl=rtl))


_bible_versions_delete = bible_versions.delete()


async def delete_bible(command: str) -> None:
    await pg.execute(_bible_versions_delete
                     .where(bible_versions.c.command == command))

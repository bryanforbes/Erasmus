from typing import List
from mypy_extensions import TypedDict
from asyncpg import Connection

from .util import select_all, select_one, insert_into, delete_from
from ..exceptions import NoUserVersionError, InvalidVersionError

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


async def get_bibles(db: Connection, *, ordered: bool = False) -> List[Bible]:
    return await select_all(db, table='bible_versions',
                            order_by=None if not ordered else 'command')


async def get_bible(db: Connection, command: str) -> Bible:
    bible = await select_one(db, command,
                             table='bible_versions',
                             where=['command = $1'])

    if not bible:
        raise InvalidVersionError(command)

    return bible


async def get_user_bible(db: Connection, user_id: int) -> Bible:
    bible = await select_one(db, str(user_id),
                             table='user_prefs',
                             joins=[('bible_versions', 'bible_versions.id = user_prefs.bible_id')],
                             where=['user_prefs.user_id = $1'])

    if bible is None:
        raise NoUserVersionError

    return bible


async def set_user_bible(db: Connection, user_id: int, bible: Bible) -> None:
    await insert_into(db, table='user_prefs',
                      values={
                          'user_id': str(user_id),
                          'bible_id': bible['id']
                      },
                      extra='''ON CONFLICT (user_id)
    DO UPDATE SET bible_id = EXCLUDED.bible_id''')


async def add_bible(db: Connection, *, command: str, name: str, abbr: str, service: str,
                    service_version: str, books: int = 3, rtl: bool = False) -> None:
    await insert_into(db, table='bible_versions',
                      values={
                          'command': command,
                          'name': name,
                          'abbr': abbr,
                          'service': service,
                          'service_version': service_version,
                          'books': books,
                          'rtl': rtl
                      })


async def delete_bible(db: Connection, command: str) -> None:
    await delete_from(db, command,
                      table='bible_versions',
                      where=['command = $1'])

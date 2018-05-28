from typing import List, Optional
from mypy_extensions import TypedDict
from botus_receptus.db import Context

from ..exceptions import InvalidVersionError

__all__ = (
    'Bible', 'get_bibles', 'get_bible', 'get_bible_by_abbr', 'get_user_bible', 'set_user_bible',
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


async def get_bibles(ctx: Context, *, ordered: bool = False) -> List[Bible]:
    return await ctx.select_all(table='bible_versions',
                                order_by=None if not ordered else 'command')


async def get_bible(ctx: Context, command: str) -> Bible:
    bible = await ctx.select_one(command, table='bible_versions', where=['command = $1'])

    if not bible:
        raise InvalidVersionError(command)

    return bible


async def get_bible_by_abbr(ctx: Context, abbr: str) -> Optional[Bible]:
    bible = await ctx.select_one(abbr, table='bible_versions', where=['command ILIKE $1'])

    if not bible:
        return None

    return bible


async def get_user_bible(ctx: Context, user_id: int) -> Bible:
    bible = await ctx.select_one(str(user_id),
                                 table='user_prefs',
                                 joins=[('bible_versions', 'bible_versions.id = user_prefs.bible_id')],
                                 where=['user_prefs.user_id = $1'])

    if bible is None:
        bible = await get_bible(ctx, 'esv')

    return bible


async def set_user_bible(ctx: Context, user_id: int, bible: Bible) -> None:
    await ctx.insert_into(table='user_prefs',
                          values={
                              'user_id': str(user_id),
                              'bible_id': bible['id']
                          },
                          extra='''ON CONFLICT (user_id)
    DO UPDATE SET bible_id = EXCLUDED.bible_id''')


async def add_bible(ctx: Context, *, command: str, name: str, abbr: str, service: str,
                    service_version: str, books: int = 3, rtl: bool = False) -> None:
    await ctx.insert_into(table='bible_versions',
                          values={
                              'command': command,
                              'name': name,
                              'abbr': abbr,
                              'service': service,
                              'service_version': service_version,
                              'books': books,
                              'rtl': rtl
                          })


async def delete_bible(ctx: Context, command: str) -> None:
    await ctx.delete_from(command,
                          table='bible_versions',
                          where=['command = $1'])

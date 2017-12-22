from typing import Sequence, List, Any, Optional, Tuple, Dict
from asyncpg import Connection

__all__ = ('select_all', 'select_one', 'insert_into', 'delete_from', 'search')


def _get_columns_string(columns: Optional[Sequence[str]]) -> str:
    if columns is None:
        return '*'

    return ', '.join(columns)


def _get_join_string(joins: Optional[Sequence[Tuple[str, str]]]) -> str:
    if joins is None or len(joins) == 0:
        return ''

    return ' ' + ' '.join(map(lambda join: f'JOIN {join[0]} ON {join[1]}', joins))


def _get_where_string(conditions: Optional[Sequence[str]]) -> str:
    if conditions is None or len(conditions) == 0:
        return ''

    return ' WHERE ' + ' AND '.join(conditions)


def _get_order_by_string(order_by: Optional[str]) -> str:
    if order_by is None:
        return ''

    return f' ORDER BY {order_by} ASC'


async def select_all(db: Connection, *args: Any,
                     columns: Optional[Sequence[str]] = None,
                     table: str,
                     order_by: Optional[str] = None,
                     where: Optional[Sequence[str]] = None,
                     joins: Optional[Sequence[Tuple[str, str]]] = None) -> List[Any]:
    columns_str = _get_columns_string(columns)
    where_str = _get_where_string(where)
    joins_str = _get_join_string(joins)
    order_by_str = _get_order_by_string(order_by)

    return await db.fetch(
        f'SELECT {columns_str} FROM {table}{joins_str}{where_str}{order_by_str}',
        *args
    )


async def select_one(db: Connection, *args: Any,
                     columns: Optional[Sequence[str]] = None,
                     table: str,
                     where: Optional[Sequence[str]],
                     joins: Optional[Sequence[Tuple[str, str]]] = None) -> Optional[Any]:
    columns_str = _get_columns_string(columns)
    joins_str = _get_join_string(joins)
    where_str = _get_where_string(where)

    return await db.fetchrow(
        f'SELECT {columns_str} FROM {table}{joins_str}{where_str}',
        *args
    )


async def search(db: Connection, *args: Any,
                 columns: Optional[Sequence[str]] = None,
                 table: str,
                 search_columns: Sequence[str],
                 terms: Sequence[str],
                 where: Sequence[str] = [],
                 order_by: Optional[str] = None,
                 joins: Optional[Sequence[Tuple[str, str]]] = None) -> List[Any]:
    columns_str = _get_columns_string(columns)
    joins_str = _get_join_string(joins)
    search_columns_str = " || ' ' || ".join(search_columns)
    search_terms_str = ' & '.join(terms)
    where_str = _get_where_string(tuple(where) + (
        f"to_tsvector('english', {search_columns_str}) @@ to_tsquery('english', '{search_terms_str}')",
    ))
    order_by_str = _get_order_by_string(order_by)

    return await db.fetch(
        f'SELECT {columns_str} FROM {table}{joins_str}{where_str}{order_by_str}',
        *args
    )


async def insert_into(db: Connection, *, table: str,
                      values: Dict[str, Any],
                      extra: str = '') -> None:
    columns: List[str] = []
    data: List[Any] = []

    for column, value in values.items():
        columns.append(column)
        data.append(value)

    if extra:
        extra = ' ' + extra

    columns_str = ', '.join(columns)
    values_str = ', '.join(map(lambda index: f'${index}', range(1, len(values) + 1)))
    await db.execute(f'INSERT INTO {table} ({columns_str}) VALUES ({values_str}){extra}', *data)


async def delete_from(db: Connection, *args: Any, table: str, where: Sequence[str]) -> None:
    where_str = _get_where_string(where)
    await db.execute(f'DELETE FROM {table}{where_str}', *args)

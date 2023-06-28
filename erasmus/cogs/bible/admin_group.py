from __future__ import annotations

from typing import TYPE_CHECKING
from typing_extensions import override

import discord
import orjson
from asyncpg.exceptions import UniqueViolationError
from botus_receptus import utils
from botus_receptus.app_commands import admin_guild_only
from discord import app_commands
from sqlalchemy.exc import IntegrityError

from ...data import SectionFlag
from ...db import BibleVersion, Session
from ...exceptions import ErasmusError
from .bible_lookup import bible_lookup

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from sqlalchemy.ext.asyncio import AsyncSession

    from ...service_manager import ServiceManager
    from .cog import Bible


def _decode_book_mapping(book_mapping: str | None) -> dict[str, str] | None:
    return orjson.loads(book_mapping) if book_mapping is not None else None


class ServiceAutoCompleter(app_commands.Transformer):
    service_manager: ServiceManager

    @override
    async def transform(self, itx: discord.Interaction, value: str, /) -> str:
        return value

    @override
    async def autocomplete(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, itx: discord.Interaction, value: str, /
    ) -> list[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=service_name, value=service_name)
            for service_name in self.service_manager.service_map
            if value.lower() in service_name.lower()
        ][:25]


_service_lookup = ServiceAutoCompleter()


@admin_guild_only()
class BibleAdminGroup(app_commands.Group, name='bibleadmin'):
    service_manager: ServiceManager
    refresh_data: Callable[[AsyncSession], Awaitable[None]]

    def initialize_from_parent(self, cog: Bible, /) -> None:
        _service_lookup.service_manager = cog.service_manager
        self.service_manager = cog.service_manager
        self.refresh_data = cog.refresh

    @app_commands.command()
    @app_commands.describe(version='The Bible version to get information for')
    async def info(
        self,
        itx: discord.Interaction,
        /,
        version: app_commands.Transform[str, bible_lookup],
    ) -> None:
        """Get information for a Bible version"""

        async with Session() as session:
            existing = await BibleVersion.get_by_command(session, version)

        await utils.send_embed(
            itx,
            title=existing.name,
            fields=[
                {'name': 'Command', 'value': existing.command},
                {'name': 'Abbreviation', 'value': existing.abbr},
                {'name': 'Right to left', 'value': 'Yes' if existing.rtl else 'No'},
                {
                    'name': 'Books',
                    'value': '\n'.join(existing.books.book_names),
                    'inline': False,
                },
                {'name': 'Service', 'value': existing.service},
                {'name': 'Service Version', 'value': existing.service_version},
            ],
        )

    @app_commands.command()
    @app_commands.describe(
        command='The unique command',
        name='The name of the Bible version',
        abbreviation='The abbreviated form of the Bible version',
        service='Service to use for lookup and search',
        service_version="The service's code for this version",
        books='Books included in this version',
        rtl='Whether text is right-to-left or not',
    )
    async def add(
        self,
        itx: discord.Interaction,
        /,
        command: str,
        name: str,
        abbreviation: str,
        service: app_commands.Transform[str, _service_lookup],
        service_version: str,
        books: str = 'OT,NT',
        rtl: bool = False,
        book_mapping: str | None = None,
    ) -> None:
        """Add a Bible version"""

        if service not in self.service_manager:
            await utils.send_embed_error(
                itx,
                description=f'`{service}` is not a valid service',
            )
            return

        try:
            async with Session.begin() as session:
                bible = BibleVersion.create(
                    command=command,
                    name=name,
                    abbr=abbreviation,
                    service=service,
                    service_version=service_version,
                    books=books,
                    rtl=rtl,
                    book_mapping=_decode_book_mapping(book_mapping),
                )
                session.add(bible)

                await session.commit()

            async with Session() as session:
                await self.refresh_data(session)
        except (UniqueViolationError, IntegrityError):
            await utils.send_embed_error(
                itx,
                description=f'`{command}` already exists',
            )
        except orjson.JSONDecodeError:
            await utils.send_embed_error(
                itx,
                description=f'`{book_mapping}` is invalid JSON',
            )
        else:
            await utils.send_embed(
                itx,
                description=f'Added `{command}` as {name!r}',
                color=discord.Colour.green(),
            )

    @app_commands.command()
    @app_commands.describe(version='The version to delete')
    async def delete(
        self,
        itx: discord.Interaction,
        /,
        version: app_commands.Transform[str, bible_lookup],
    ) -> None:
        """Delete a Bible"""

        async with Session.begin() as session:
            existing = await BibleVersion.get_by_command(session, version)
            bible_lookup.discard(existing.command)
            await session.delete(existing)

        await utils.send_embed(
            itx,
            description=f'Removed `{existing.command}`',
        )

    @app_commands.command()
    @app_commands.describe(
        version='The version to update',
        service='Service to use for lookup and search',
        service_version="The service's code for this version",
    )
    async def update(
        self,
        itx: discord.Interaction,
        /,
        version: app_commands.Transform[str, bible_lookup],
        name: str | None = None,
        abbreviation: str | None = None,
        service: app_commands.Transform[  # noqa: RUF013
            str | None, _service_lookup
        ] = None,
        service_version: str | None = None,
        rtl: bool | None = None,
        books: str | None = None,
        book_mapping: str | None = None,
    ) -> None:
        """Update a Bible"""

        if service is not None and service not in self.service_manager:
            await utils.send_embed_error(
                itx,
                description=f'`{service}` is not a valid service',
            )
            return

        try:
            async with Session.begin() as session:
                bible = await BibleVersion.get_by_command(session, version)

                if name is not None:
                    bible.name = name

                if abbreviation is not None:
                    bible.abbr = abbreviation

                if service is not None:
                    bible.service = service

                if service_version is not None:
                    bible.service_version = service_version

                if rtl is not None:
                    bible.rtl = rtl

                if books is not None:
                    bible.books = SectionFlag.from_book_names(books)

                if book_mapping is not None:
                    bible.book_mapping = _decode_book_mapping(book_mapping)

                await session.commit()

            async with Session() as session:
                await self.refresh_data(session)
        except orjson.JSONDecodeError:
            await utils.send_embed_error(
                itx,
                description=f'`{book_mapping}` is invalid JSON',
            )
        except ErasmusError:
            raise
        except Exception:  # noqa: BLE001
            await utils.send_embed_error(itx, description=f'Error updating `{version}`')
        else:
            await utils.send_embed(itx, description=f'Updated `{version}`')

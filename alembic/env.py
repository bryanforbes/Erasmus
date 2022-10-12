from __future__ import annotations, with_statement

import asyncio
from logging.config import fileConfig
from pathlib import Path
from typing import TYPE_CHECKING, Any

from alembic import context
from botus_receptus.config import load
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config  # type: ignore
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

import erasmus.json
from erasmus.db.base import _mapper_registry

if TYPE_CHECKING:
    from alembic.operations.ops import MigrationScript
    from alembic.runtime.migration import MigrationContext

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = _mapper_registry.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

bot_config = load(Path(__file__).resolve().parent.parent / 'config.toml')


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = bot_config.get('db_url', '')

    context.configure(  # type: ignore
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
    )

    with context.begin_transaction():  # type: ignore
        context.run_migrations()  # type: ignore


def _do_run_migrations(connection: AsyncConnection) -> None:
    def process_revision_directives(
        context: MigrationContext, revision: Any, directives: list[MigrationScript]
    ):
        if config.cmd_opts is not None and config.cmd_opts.autogenerate:
            script = directives[0]
            if (
                script.upgrade_ops is not None  # type: ignore
                and script.upgrade_ops.is_empty()  # type: ignore
            ):
                directives[:] = []

    context.configure(  # type: ignore
        connection=connection,  # type: ignore
        target_metadata=target_metadata,
        process_revision_directives=process_revision_directives,
    )

    with context.begin_transaction():  # type: ignore
        context.run_migrations()  # type: ignore


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    connectable: AsyncEngine = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
        url=bot_config.get('db_url', ''),
        json_serializer=erasmus.json.serialize,
        json_deserializer=erasmus.json.deserialize,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(_do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())

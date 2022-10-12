"""Rename 1689

Revision ID: d20ba96e7d26
Revises: cdf53768de2d
Create Date: 2022-09-09 14:46:04.418800

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'd20ba96e7d26'
down_revision = 'cdf53768de2d'
branch_labels = None
depends_on = None


confessions = sa.table(
    'confessions',
    sa.column('command', sa.String),
    sa.column('name', sa.String),
)


def upgrade():
    op.execute(
        confessions.update()
        .filter(confessions.c.command == '1689')
        .values(name='The London Baptist Confession of Faith (1689)')
    )


def downgrade():
    op.execute(
        confessions.update()
        .filter(confessions.c.command == '1689')
        .values(name='The Second London Baptist Confession of Faith')
    )

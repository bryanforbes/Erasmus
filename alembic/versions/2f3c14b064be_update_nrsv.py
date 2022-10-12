"""Update NRSV

Revision ID: 2f3c14b064be
Revises: d20ba96e7d26
Create Date: 2022-09-22 15:06:32.342532

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '2f3c14b064be'
down_revision = 'd20ba96e7d26'
branch_labels = None
depends_on = None

bible_versions = sa.table(
    'bible_versions',
    sa.column('id', sa.Integer),
    sa.column('command', sa.String),
    sa.column('name', sa.String),
    sa.column('abbr', sa.String),
    sa.column('service', sa.String),
    sa.column('service_version', sa.String),
    sa.column('rtl', sa.Boolean),
    sa.column('books', sa.BigInteger),
)


def upgrade():
    op.execute(
        bible_versions.update()
        .filter(bible_versions.c.command == 'nrsv')
        .values({'service_version': 'NRSVue'})
    )


def downgrade():
    op.execute(
        bible_versions.update()
        .filter(bible_versions.c.command == 'nrsv')
        .values({'service_version': 'NRSV'})
    )

"""Add LBCF 1646

Revision ID: cdf53768de2d
Revises: 830329e85f73
Create Date: 2022-08-23 17:29:56.224699

"""
from pathlib import Path

import sqlalchemy as sa
from orjson import loads
from sqlalchemy.sql import column, table

from alembic import op

# revision identifiers, used by Alembic.
revision = 'cdf53768de2d'
down_revision = '830329e85f73'
branch_labels = None
depends_on = None

with (Path(__file__).resolve().parent / f'{revision}_keach.json').open() as f:
    keach_data = loads(f.read())


confessions = table(
    'confessions',
    column('id', sa.Integer),
    column('command', sa.String),
    column('name', sa.String),
    column('type_id', sa.Integer, sa.ForeignKey('confession_types.id')),
    column('numbering_id', sa.Integer, sa.ForeignKey('confession_numbering_types.id')),
)

articles = table(
    'confession_articles',
    column('id', sa.Integer),
    column('article_number', sa.Integer),
    column('title', sa.Text),
    column('text', sa.Text),
)


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

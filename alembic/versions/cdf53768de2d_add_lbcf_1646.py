"""Add LBCF 1646

Revision ID: cdf53768de2d
Revises: 830329e85f73
Create Date: 2022-08-23 17:29:56.224699

"""
from pathlib import Path

import sqlalchemy as sa
from orjson import loads
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.sql import column, table

from alembic import op
from erasmus.db.confession import ConfessionType, NumberingType

# revision identifiers, used by Alembic.
revision = 'cdf53768de2d'
down_revision = '1f333584607a'
branch_labels = None
depends_on = None

with (Path(__file__).resolve().parent / f'{revision}_add_lbcf_1646.json').open() as f:
    keach_data = loads(f.read())


confessions = table(
    'confessions',
    column('id', sa.Integer),
    column('command', sa.String),
    column('name', sa.String),
    column('type', ENUM(ConfessionType)),
    column('numbering', ENUM(NumberingType)),
)

sections = table(
    'confession_sections',
    column('id', sa.Integer),
    column('confession_id', sa.Integer, sa.ForeignKey('confessions.id')),
    column('number', sa.Integer),
    column('text', sa.Text),
)


def upgrade() -> None:
    lbcf_1646 = op.bulk_insert(
        confessions,
        [
            {
                'command': 'lbcf46',
                'name': 'The London Baptist Confession of Faith (1646)',
                'type': ConfessionType.ARTICLES,
                'numbering': NumberingType.ROMAN,
            }
        ],
    )


def downgrade() -> None:
    conn = op.get_bind()

"""Add LBCF 1646

Revision ID: cdf53768de2d
Revises: 830329e85f73
Create Date: 2022-08-23 17:29:56.224699

"""
from pathlib import Path

import sqlalchemy as sa
from orjson import loads
from sqlalchemy.dialects.postgresql import ENUM

from alembic import op
from erasmus.db.confession import ConfessionType, NumberingType

# revision identifiers, used by Alembic.
revision = 'cdf53768de2d'
down_revision = '7b16df83859b'
branch_labels = None
depends_on = None

with (Path(__file__).resolve().parent / f'{revision}_add_lbcf_1646.json').open() as f:
    lbcf_data = loads(f.read())


metadata = sa.MetaData()

confessions = sa.Table(
    'confessions',
    metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('command', sa.String, unique=True, nullable=False),
    sa.Column('name', sa.String, nullable=False),
    sa.Column('type', ENUM(ConfessionType, name='confession_type'), nullable=False),
    sa.Column(
        'numbering',
        ENUM(NumberingType, name='confession_numbering_type'),
        nullable=False,
    ),
    sa.Column(
        'subsection_numbering',
        ENUM(NumberingType, name='confession_numbering_type'),
        nullable=True,
    ),
)

sections = sa.Table(
    'confession_sections',
    metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column(
        'confession_id', sa.Integer, sa.ForeignKey('confessions.id'), nullable=False
    ),
    sa.Column('number', sa.Integer, nullable=False),
    sa.Column('subsection_number', sa.Integer),
    sa.Column('title', sa.Text),
    sa.Column('text', sa.Text, nullable=False),
)


def upgrade() -> None:
    conn = op.get_bind()

    op.bulk_insert(
        confessions,
        [
            {
                'command': 'lbcf46',
                'name': lbcf_data['title'],
                'type': ConfessionType.SECTIONS,
                'numbering': NumberingType.ROMAN,
            }
        ],
    )

    lbcf = conn.execute(
        sa.select(confessions).filter(confessions.c.command == 'lbcf46')
    ).fetchone()

    op.bulk_insert(
        sections,
        [
            {'confession_id': lbcf['id'], 'number': index, 'text': section}
            for index, section in enumerate(lbcf_data['sections'], 1)
        ],
    )


def downgrade() -> None:
    conn = op.get_bind()

    lbcf = conn.execute(
        sa.select(confessions).filter(confessions.c.command == 'lbcf46')
    ).fetchone()
    op.execute(sections.delete().filter(sections.c.confession_id == lbcf['id']))
    op.execute(confessions.delete().filter(confessions.c.command == 'lbcf46'))

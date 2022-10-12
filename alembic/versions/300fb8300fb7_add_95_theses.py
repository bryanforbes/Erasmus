"""Add 95 Theses

Revision ID: 300fb8300fb7
Revises: 902fb954c12f
Create Date: 2022-09-28 16:53:12.660808

"""
from __future__ import annotations

from json import load
from pathlib import Path

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from erasmus.db.confession import ConfessionType, NumberingType

# revision identifiers, used by Alembic.
revision = '300fb8300fb7'
down_revision = '902fb954c12f'
branch_labels = None
depends_on = None


confessions = sa.table(
    'confessions',
    sa.column('id', sa.Integer),
    sa.column('command', sa.String),
    sa.column('name', sa.String),
    sa.column('type', postgresql.ENUM(ConfessionType, name='confession_type')),
    sa.column(
        'numbering',
        postgresql.ENUM(NumberingType, name='confession_numbering_type'),
    ),
)

confession_sections = sa.table(
    'confession_sections',
    sa.column('confession_id', sa.Integer),
    sa.column('number', sa.Integer),
    sa.column('title', sa.Text),
    sa.column('text', sa.Text),
)


def upgrade():
    conn = op.get_bind()

    with (
        Path(__file__).resolve().parent / f'{revision}_add_95_theses.json'
    ).open() as f:
        data = load(f)

    op.bulk_insert(
        confessions,
        [
            {
                'command': '95t',
                'name': data['title'],
                'type': ConfessionType.SECTIONS,
                'numbering': NumberingType.ARABIC,
            }
        ],
    )

    confession = conn.execute(
        sa.select(confessions).filter(confessions.c.command == '95t')
    ).fetchone()

    op.bulk_insert(
        confession_sections,
        [
            {
                'confession_id': confession['id'],
                'number': index,
                'text': text,
            }
            for index, text in enumerate(data['sections'], start=1)
        ],
    )


def downgrade():
    conn = op.get_bind()

    confession = conn.execute(
        sa.select(confessions).filter(confessions.c.command == '95t')
    ).fetchone()

    op.execute(
        confession_sections.delete().filter(
            confession_sections.c.confession_id == confession['id']
        )
    )
    op.execute(confessions.delete().filter(confessions.c.command == '95t'))

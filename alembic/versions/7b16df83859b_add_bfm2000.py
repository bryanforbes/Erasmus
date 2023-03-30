"""Add BFM2000

Revision ID: 7b16df83859b
Revises: f4981c5dda24
Create Date: 2022-08-29 17:05:14.518278

"""
from __future__ import annotations

from json import load
from pathlib import Path

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from erasmus.db.enums import ConfessionType, NumberingType

# revision identifiers, used by Alembic.
revision = '7b16df83859b'
down_revision = 'f4981c5dda24'
branch_labels = None
depends_on = None

metadata = sa.MetaData()
confessions = sa.Table(
    'confessions',
    metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('command', sa.String, unique=True, nullable=False),
    sa.Column('name', sa.String, nullable=False),
    sa.Column(
        'type', postgresql.ENUM(ConfessionType, name='confession_type'), nullable=False
    ),
    sa.Column(
        'numbering',
        postgresql.ENUM(NumberingType, name='confession_numbering_type'),
        nullable=False,
    ),
    sa.Column(
        'subsection_numbering',
        postgresql.ENUM(NumberingType, name='confession_numbering_type'),
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


def upgrade():
    conn = op.get_bind()

    with op.get_context().autocommit_block():
        op.execute(
            "SELECT setval('confessions_id_seq', ("
            "SELECT MAX(confessions.id) from confessions"
            "))"
        )

        op.execute("ALTER TYPE confession_type ADD VALUE IF NOT EXISTS 'SECTIONS'")
        op.execute(
            "ALTER TYPE confession_numbering_type ADD VALUE IF NOT EXISTS 'ALPHA'"
        )

    op.add_column(
        'confessions',
        sa.Column(
            'subsection_numbering',
            postgresql.ENUM(
                'ARABIC', 'ROMAN', 'ALPHA', name='confession_numbering_type'
            ),
            nullable=True,
        ),
    )

    with (Path(__file__).resolve().parent / f'{revision}_bfm2000.json').open() as f:
        data = load(f)

    op.bulk_insert(
        confessions,
        [
            {
                'command': 'bfm2k',
                'name': data['title'],
                'type': ConfessionType.SECTIONS,
                'numbering': NumberingType.ARABIC,
                'subsection_numbering': NumberingType.ALPHA,
            }
        ],
    )

    bfm2k = conn.execute(
        sa.select(confessions).filter(confessions.c.command == 'bfm2k')
    ).fetchone()

    op.bulk_insert(
        sections,
        [
            {
                'confession_id': bfm2k['id'],
                'title': section['title'],
                'number': section['number'],
                'subsection_number': section.get('subsection_number'),
                'text': section['text'],
            }
            for section in data['sections']
        ],
    )


def downgrade():
    conn = op.get_bind()

    bfm2k = conn.execute(
        sa.select(confessions).filter(confessions.c.command == 'bfm2k')
    ).fetchone()

    op.execute(sections.delete().filter(sections.c.confession_id == bfm2k['id']))
    op.execute(confessions.delete().filter(confessions.c.command == 'bfm2k'))
    op.drop_column('confessions', 'subsection_numbering')

    op.execute(
        'ALTER TYPE confession_numbering_type RENAME TO confession_numbering_type_old'
    )
    op.execute("CREATE TYPE confession_numbering_type AS ENUM('ARABIC', 'ROMAN')")
    op.execute(
        'ALTER TABLE confessions ALTER COLUMN numbering TYPE confession_numbering_type '
        'USING numbering::text::confession_numbering_type'
    )
    op.execute('DROP TYPE confession_numbering_type_old')

    op.execute('ALTER TYPE confession_type RENAME TO confession_type_old')
    op.execute("CREATE TYPE confession_type AS ENUM('ARTICLES', 'CHAPTERS', 'QA')")
    op.execute(
        'ALTER TABLE confessions ALTER COLUMN type TYPE confession_type '
        'USING type::text::confession_type'
    )
    op.execute('DROP TYPE confession_type_old')

    op.execute(
        "SELECT setval('confessions_id_seq', ("
        "SELECT MAX(confessions.id) from confessions"
        "))"
    )

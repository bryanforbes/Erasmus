"""Add confessions tables and 1689

Revision ID: 69e765223549
Revises: e7aff6447fbe
Create Date: 2017-10-10 20:13:10.688722

"""
from __future__ import annotations

from collections import OrderedDict
from json import load
from pathlib import Path

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '69e765223549'
down_revision = 'e7aff6447fbe'
branch_labels = None
depends_on = None

with (Path(__file__).resolve().parent / f'{revision}_1689.json').open() as f:
    lbcf_data = load(f, object_pairs_hook=lambda x: OrderedDict(x))


def upgrade():
    confessions = op.create_table(
        'confessions',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('command', sa.String, unique=True),
        sa.Column('name', sa.String),
    )

    confession_chapters = op.create_table(
        'confession_chapters',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('confession_id', sa.Integer, sa.ForeignKey('confessions.id')),
        sa.Column('chapter_number', sa.Integer),
        sa.Column('title', sa.String),
    )

    confession_paragraphs = op.create_table(
        'confession_paragraphs',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('confession_id', sa.Integer, sa.ForeignKey('confessions.id')),
        sa.Column('chapter_number', sa.Integer),
        sa.Column('paragraph_number', sa.Integer),
        sa.Column('text', sa.Text),
    )

    conn = op.get_bind()

    result = conn.execute(
        confessions.insert(),
        {'command': '1689', 'name': 'The Second London Baptist Confession of Faith'},
    )

    confession_id = result.inserted_primary_key[0]

    for chapter_str, chapter in lbcf_data['chapters'].items():
        chapter_number = int(chapter_str)
        conn.execute(
            confession_chapters.insert(),
            {
                'confession_id': confession_id,
                'chapter_number': chapter_number,
                'title': chapter['title'],
            },
        )
        conn.execute(
            confession_paragraphs.insert(),
            *[
                {
                    'confession_id': confession_id,
                    'chapter_number': chapter_number,
                    'paragraph_number': int(paragraph_str),
                    'text': text,
                }
                for paragraph_str, text in chapter['paragraphs'].items()
            ],
        )


def downgrade():
    op.drop_table('confession_paragraphs')
    op.drop_table('confession_chapters')
    op.drop_table('confessions')

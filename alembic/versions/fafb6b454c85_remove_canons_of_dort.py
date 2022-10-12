"""Remove Canons of Dort

Revision ID: fafb6b454c85
Revises: 43c0cf2239c4
Create Date: 2017-10-12 20:24:33.952909

"""
from __future__ import annotations

from collections import OrderedDict
from json import load
from pathlib import Path

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'fafb6b454c85'
down_revision = '43c0cf2239c4'
branch_labels = None
depends_on = None

with (Path(__file__).resolve().parent / f'{down_revision}_dort.json').open() as f:
    dort_data = load(f, object_pairs_hook=lambda x: OrderedDict(x))

metadata = sa.MetaData()

confessions = sa.Table(
    'confessions',
    metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('command', sa.String, unique=True),
    sa.Column('name', sa.String),
)

confession_chapters = sa.Table(
    'confession_chapters',
    metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('confession_id', sa.Integer, sa.ForeignKey('confessions.id')),
    sa.Column('chapter_number', sa.Integer),
    sa.Column('title', sa.String),
)

confession_paragraphs = sa.Table(
    'confession_paragraphs',
    metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('confession_id', sa.Integer, sa.ForeignKey('confessions.id')),
    sa.Column('chapter_number', sa.Integer),
    sa.Column('paragraph_number', sa.Integer),
    sa.Column('text', sa.Text),
)


def upgrade():
    conn = op.get_bind()

    result = conn.execute(confessions.select().where(confessions.c.command == 'dort'))
    row = result.fetchone()

    conn.execute(
        confession_paragraphs.delete().where(
            confession_paragraphs.c.confession_id == row['id']
        )
    )
    conn.execute(
        confession_chapters.delete().where(
            confession_chapters.c.confession_id == row['id']
        )
    )
    conn.execute(confessions.delete().where(confessions.c.id == row['id']))

    result.close()


def downgrade():
    conn = op.get_bind()

    result = conn.execute(
        confessions.insert(), {'command': 'dort', 'name': 'The Canons of Dort'}
    )

    confession_id = result.inserted_primary_key[0]

    for chapter_str, chapter in dort_data['chapters'].items():
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

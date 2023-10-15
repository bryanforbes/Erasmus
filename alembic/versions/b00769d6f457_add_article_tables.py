"""Add article tables

Revision ID: b00769d6f457
Revises: 0f780af615ef
Create Date: 2017-10-15 13:16:36.512159

"""
from __future__ import annotations

from collections import OrderedDict
from json import load
from pathlib import Path
from typing import Any, TypedDict

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import column, table

# revision identifiers, used by Alembic.
revision = 'b00769d6f457'
down_revision = '0f780af615ef'
branch_labels = None
depends_on = None

confesses = table(
    'confesses',
    column('id', sa.Integer),
    column('command', sa.String),
    column('name', sa.String),
    column('type_id', sa.Integer, sa.ForeignKey('confess_types.id')),
    column('numbering_id', sa.Integer, sa.ForeignKey('confess_numbering_type.id')),
)


class ArticlesJSON(TypedDict):
    title: str
    articles: list[list[str]]


def _get_article_records(id: str, data: ArticlesJSON) -> list[dict[str, Any]]:
    articles: list[dict[str, Any]] = []

    for index in range(len(data['articles'])):
        title, text = data['articles'][index]
        articles.append(
            {
                'confess_id': id,
                'article_number': index + 1,
                'title': title,
                'text': text,
            }
        )

    return articles


def upgrade():
    op.alter_column('confess_paragraphs', 'chapter_number', nullable=False)

    confess_numbering_type = op.create_table(
        'confess_numbering_type',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('numbering', sa.String(20), unique=True, nullable=False),
    )

    confess_articles = op.create_table(
        'confess_articles',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column(
            'confess_id', sa.Integer, sa.ForeignKey('confesses.id'), nullable=False
        ),
        sa.Column('article_number', sa.Integer, nullable=False),
        sa.Column('title', sa.String, nullable=False),
        sa.Column('text', sa.Text, nullable=False),
        sa.Index(
            'confess_articles_text_idx',
            sa.func.to_tsvector('english', 'text'),
            postgresql_using='gin',
        ),
    )

    op.bulk_insert(
        confess_numbering_type,
        [{'id': 1, 'numbering': 'ARABIC'}, {'id': 2, 'numbering': 'ROMAN'}],
    )

    op.add_column(
        'confesses',
        sa.Column(
            'numbering_id', sa.Integer, sa.ForeignKey('confess_numbering_type.id')
        ),
    )

    op.execute('UPDATE confesses set numbering_id = 1;')

    op.alter_column('confesses', 'numbering_id', nullable=False)

    op.bulk_insert(
        confesses,
        [
            {
                'id': 6,
                'command': 'bcf',
                'type_id': 1,
                'numbering_id': 1,
                'name': 'The Belgic Confession of Faith',
            },
            {
                'id': 7,
                'command': '39a',
                'type_id': 1,
                'numbering_id': 2,
                'name': 'The 39 Articles',
            },
        ],
    )

    with (Path(__file__).resolve().parent / f'{revision}_bcf.json').open() as f:
        bcf_data = load(f, object_pairs_hook=lambda x: OrderedDict(x))

    with (Path(__file__).resolve().parent / f'{revision}_articles.json').open() as f:
        thirty_nine_data = load(f, object_pairs_hook=lambda x: OrderedDict(x))

    op.bulk_insert(
        confess_articles,
        _get_article_records(6, bcf_data) + _get_article_records(7, thirty_nine_data),
    )


def downgrade():
    op.execute(confesses.delete().where(confesses.c.type_id == 1))
    op.drop_column('confesses', 'numbering_id')
    op.drop_table('confess_articles')
    op.drop_table('confess_numbering_type')
    op.alter_column('confess_paragraphs', 'chapter_number', nullable=True)

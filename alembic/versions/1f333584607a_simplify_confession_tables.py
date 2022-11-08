"""Simplify confession tables

Revision ID: 1f333584607a
Revises: a882aec7c9e4
Create Date: 2022-08-27 09:42:15.737664

"""
from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from alembic import op

from erasmus.db.types import TSVector

# revision identifiers, used by Alembic.
revision = '1f333584607a'
down_revision = 'a882aec7c9e4'
branch_labels = None
depends_on = None

metadata = sa.MetaData()

chapters = sa.Table(
    'confession_chapters',
    metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column(
        'confess_id', sa.Integer, sa.ForeignKey('confessions.id'), nullable=False
    ),
    sa.Column('chapter_number', sa.Integer, nullable=False),
    sa.Column('chapter_title', sa.String, nullable=False),
)

paragraphs = sa.Table(
    'confession_paragraphs',
    metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column(
        'confess_id', sa.Integer, sa.ForeignKey('confessions.id'), nullable=False
    ),
    sa.Column('chapter_number', sa.Integer, nullable=False),
    sa.Column('paragraph_number', sa.Integer, nullable=False),
    sa.Column('text', sa.Text, nullable=False),
)

questions = sa.Table(
    'confession_questions',
    metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column(
        'confess_id', sa.Integer, sa.ForeignKey('confessions.id'), nullable=False
    ),
    sa.Column('question_number', sa.Integer, nullable=False),
    sa.Column('question_text', sa.Text, nullable=False),
    sa.Column('answer_text', sa.Text, nullable=False),
)

articles = sa.Table(
    'confession_articles',
    metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column(
        'confess_id', sa.Integer, sa.ForeignKey('confessions.id'), nullable=False
    ),
    sa.Column('article_number', sa.Integer, nullable=False),
    sa.Column('title', sa.Text, nullable=False),
    sa.Column('text', sa.Text, nullable=False),
)


def upgrade():
    conn = op.get_bind()

    sections = op.create_table(
        'confession_sections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('number', sa.Integer(), nullable=False),
        sa.Column('subsection_number', sa.Integer(), nullable=True),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column(
            'search_vector',
            TSVector(),
            sa.Computed(
                "to_tsvector('english', trim(coalesce(title, '') || ' ' || text, ' '))",
            ),
            nullable=True,
        ),
        sa.Column('confession_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['confession_id'],
            ['confessions.id'],
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'confession_sections_search_idx',
        'confession_sections',
        ['search_vector'],
        unique=False,
        postgresql_using='gin',
    )

    section_data: list[dict[str, Any]] = []

    # convert chapters/paragraphs to sections
    result = conn.execute(
        sa.select(paragraphs, chapters).select_from(
            sa.join(
                paragraphs,
                chapters,
                sa.and_(
                    paragraphs.c.chapter_number == chapters.c.chapter_number,
                    paragraphs.c.confess_id == chapters.c.confess_id,
                ),
            )
        )
    )

    for row in result:
        section_data.append(
            {
                'confession_id': row['confess_id'],
                'number': row['chapter_number'],
                'subsection_number': row['paragraph_number'],
                'title': row['chapter_title'],
                'text': row['text'],
            }
        )

    # convert questions to sections
    result = conn.execute(sa.select(questions))

    for row in result:
        section_data.append(
            {
                'confession_id': row['confess_id'],
                'number': row['question_number'],
                'subsection_number': None,
                'title': row['question_text'],
                'text': row['answer_text'],
            }
        )

    # convert articles to sections
    result = conn.execute(sa.select(articles))

    for row in result:
        section_data.append(
            {
                'confession_id': row['confess_id'],
                'number': row['article_number'],
                'subsection_number': None,
                'title': row['title'],
                'text': row['text'],
            }
        )

    op.bulk_insert(sections, section_data)


def downgrade():
    op.drop_index(
        'confession_sections_search_idx',
        table_name='confession_sections',
        postgresql_using='gin',
    )
    op.drop_table('confession_sections')

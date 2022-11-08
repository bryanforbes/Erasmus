"""Remove old confession tables

Revision ID: f4981c5dda24
Revises: 1f333584607a
Create Date: 2022-09-08 17:48:28.827595

"""
from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from alembic import op
from botus_receptus.sqlalchemy import TSVector
from sqlalchemy.dialects.postgresql import ENUM

from erasmus.db.enums import ConfessionType, NumberingType

# revision identifiers, used by Alembic.
revision = 'f4981c5dda24'
down_revision = '1f333584607a'
branch_labels = None
depends_on = None

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
    op.drop_index(
        'confession_questions_search_idx',
        table_name='confession_questions',
        postgresql_using='gin',
    )
    op.drop_table('confession_questions')
    op.drop_table('confession_chapters')
    op.drop_index(
        'confession_articles_search_idx',
        table_name='confession_articles',
        postgresql_using='gin',
    )
    op.drop_table('confession_articles')
    op.drop_index(
        'confession_paragraphs_text_idx',
        table_name='confession_paragraphs',
        postgresql_using='gin',
    )
    op.drop_table('confession_paragraphs')


def downgrade():
    paragraphs = op.create_table(
        'confession_paragraphs',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('confess_id', sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column('chapter_number', sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column(
            'paragraph_number', sa.INTEGER(), autoincrement=False, nullable=False
        ),
        sa.Column('text', sa.TEXT(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(
            ['confess_id'],
            ['confessions.id'],
            name='confession_paragraphs_confess_id_fkey',
        ),
        sa.PrimaryKeyConstraint('id', name='confession_paragraphs_pkey'),
    )
    op.create_index(
        'confession_paragraphs_text_idx',
        'confession_paragraphs',
        [sa.text("to_tsvector('english', text)")],
        postgresql_using='gin',
    )
    articles = op.create_table(
        'confession_articles',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('confess_id', sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column('article_number', sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column('title', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('text', sa.TEXT(), autoincrement=False, nullable=False),
        sa.Column(
            'search_vector',
            TSVector(),
            sa.Computed(
                "to_tsvector('english'::regconfig, "
                "(((title)::text || ' '::text) || text))",
                persisted=True,
            ),
            autoincrement=False,
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ['confess_id'],
            ['confessions.id'],
            name='confession_articles_confess_id_fkey',
        ),
        sa.PrimaryKeyConstraint('id', name='confession_articles_pkey'),
    )
    op.create_index(
        'confession_articles_search_idx',
        'confession_articles',
        ['search_vector'],
        unique=False,
        postgresql_using='gin',
    )
    chapters = op.create_table(
        'confession_chapters',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('confess_id', sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column('chapter_number', sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column('chapter_title', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(
            ['confess_id'],
            ['confessions.id'],
            name='confession_chapters_confess_id_fkey',
        ),
        sa.PrimaryKeyConstraint('id', name='confession_chapters_pkey'),
    )
    questions = op.create_table(
        'confession_questions',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('confess_id', sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column('question_number', sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column('question_text', sa.TEXT(), autoincrement=False, nullable=False),
        sa.Column('answer_text', sa.TEXT(), autoincrement=False, nullable=False),
        sa.Column(
            'search_vector',
            TSVector(),
            sa.Computed(
                "to_tsvector('english'::regconfig, "
                "((question_text || ' '::text) || answer_text))",
                persisted=True,
            ),
            autoincrement=False,
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ['confess_id'],
            ['confessions.id'],
            name='confession_questions_confess_id_fkey',
        ),
        sa.PrimaryKeyConstraint('id', name='confession_questions_pkey'),
    )
    op.create_index(
        'confession_questions_search_idx',
        'confession_questions',
        ['search_vector'],
        unique=False,
        postgresql_using='gin',
    )

    article_data: list[dict[str, Any]] = []
    question_data: list[dict[str, Any]] = []
    chapter_data: list[dict[str, Any]] = []
    paragraph_data: list[dict[str, Any]] = []

    conn = op.get_bind()
    confession_rows = conn.execute(sa.select(confessions))

    for confession in confession_rows:
        section_rows = conn.execute(
            sa.select(sections)
            .filter(sections.c.confession_id == confession['id'])
            .order_by(sections.c.number.asc(), sections.c.subsection_number.asc())
        )

        if confession['type'] == ConfessionType.CHAPTERS:
            chapter_numbers: set[int] = set()
            for section in section_rows:
                if section['number'] not in chapter_numbers:
                    chapter_data.append(
                        {
                            'confess_id': confession['id'],
                            'chapter_number': section['number'],
                            'chapter_title': section['title'],
                        }
                    )
                    chapter_numbers.add(section['number'])

                paragraph_data.append(
                    {
                        'confess_id': confession['id'],
                        'chapter_number': section['number'],
                        'paragraph_number': section['subsection_number'],
                        'text': section['text'],
                    }
                )
        else:
            for section in section_rows:
                if confession['type'] == ConfessionType.ARTICLES:
                    article_data.append(
                        {
                            'confess_id': confession['id'],
                            'article_number': section['number'],
                            'title': section['title'],
                            'text': section['text'],
                        }
                    )
                elif confession['type'] == ConfessionType.QA:
                    question_data.append(
                        {
                            'confess_id': confession['id'],
                            'question_number': section['number'],
                            'question_text': section['title'],
                            'answer_text': section['text'],
                        }
                    )

    op.bulk_insert(articles, article_data)
    op.bulk_insert(questions, question_data)
    op.bulk_insert(chapters, chapter_data)
    op.bulk_insert(paragraphs, paragraph_data)

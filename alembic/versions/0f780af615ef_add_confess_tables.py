"""Add 'confess*' tables

Revision ID: 0f780af615ef
Revises: ac322afa9c4d
Create Date: 2017-10-14 14:23:35.966456

"""

from __future__ import annotations

from collections import OrderedDict
from json import load
from pathlib import Path
from typing import Any, TypedDict

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '0f780af615ef'
down_revision = 'ac322afa9c4d'
branch_labels = None
depends_on = None


class ChapterJSON(TypedDict):
    title: str
    paragraphs: dict[str, str]


class ConfessionJSON(TypedDict):
    title: str
    chapters: dict[str, ChapterJSON]


class QAJSON(TypedDict):
    title: str
    questions: list[list[str]]


def _get_paragraph_records(
    id: str, data: ConfessionJSON
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    chapters: list[dict[str, Any]] = []
    paragraphs: list[dict[str, Any]] = []

    for chapter_str, chapter in data['chapters'].items():
        chapter_number = int(chapter_str)

        chapters.append(
            {
                'confess_id': id,
                'chapter_number': chapter_number,
                'chapter_title': chapter['title'],
            }
        )
        paragraphs += [
            {
                'confess_id': id,
                'chapter_number': chapter_number,
                'paragraph_number': int(paragraph_str),
                'text': text,
            }
            for paragraph_str, text in chapter['paragraphs'].items()
        ]

    return (chapters, paragraphs)


def _get_qa_records(id: str, data: QAJSON) -> list[dict[str, Any]]:
    qas: list[dict[str, Any]] = []

    for index in range(len(data['questions'])):
        question, answer = data['questions'][index]
        qas.append(
            {
                'confess_id': id,
                'question_number': index + 1,
                'question_text': question,
                'answer_text': answer,
            }
        )

    return qas


def upgrade():
    types = op.create_table(
        'confess_types',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('value', sa.String(20), unique=True, nullable=False),
    )

    confesses = op.create_table(
        'confesses',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('command', sa.String, unique=True, nullable=False),
        sa.Column('name', sa.String, nullable=False),
        sa.Column(
            'type_id', sa.Integer, sa.ForeignKey('confess_types.id'), nullable=False
        ),
    )

    chapters = op.create_table(
        'confess_chapters',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column(
            'confess_id', sa.Integer, sa.ForeignKey('confesses.id'), nullable=False
        ),
        sa.Column('chapter_number', sa.Integer, nullable=False),
        sa.Column('chapter_title', sa.String, nullable=False),
    )

    paragraphs = op.create_table(
        'confess_paragraphs',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column(
            'confess_id', sa.Integer, sa.ForeignKey('confesses.id'), nullable=False
        ),
        sa.Column('chapter_number', sa.Integer),
        sa.Column('paragraph_number', sa.Integer, nullable=False),
        sa.Column('text', sa.Text, nullable=False),
    )

    op.create_index(
        'confess_paragraphs_text_idx',
        'confess_paragraphs',
        [sa.text("to_tsvector('english', text)")],
        postgresql_using='gin',
    )

    qas = op.create_table(
        'confess_qas',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column(
            'confess_id', sa.Integer, sa.ForeignKey('confesses.id'), nullable=False
        ),
        sa.Column('question_number', sa.Integer, nullable=False),
        sa.Column('question_text', sa.Text, nullable=False),
        sa.Column('answer_text', sa.Text, nullable=False),
    )

    op.create_index(
        'confess_qas_text_idx',
        'confess_qas',
        [sa.text("to_tsvector('english', question_text || ' ' || answer_text)")],
        postgresql_using='gin',
    )

    op.bulk_insert(
        types,
        [
            {'id': 1, 'value': 'ARTICLES'},
            {'id': 2, 'value': 'CHAPTERS'},
            {'id': 3, 'value': 'QA'},
        ],
    )

    op.bulk_insert(
        confesses,
        [
            {
                'id': 1,
                'command': '1689',
                'type_id': 2,
                'name': 'The Second London Baptist Confession of Faith',
            },
            {
                'id': 2,
                'command': 'wcf',
                'type_id': 2,
                'name': 'The Westminster Confession of Faith',
            },
            {
                'id': 3,
                'command': 'wsc',
                'type_id': 3,
                'name': 'The Wesminster Shorter Catechism',
            },
            {
                'id': 4,
                'command': 'wlc',
                'type_id': 3,
                'name': 'The Wesminster Longer Catechism',
            },
            {
                'id': 5,
                'command': 'hc',
                'type_id': 3,
                'name': 'The Heidelberg Catechism',
            },
        ],
    )

    with (Path(__file__).resolve().parent / '69e765223549_1689.json').open() as f:
        lbcf_data = load(f, object_pairs_hook=lambda x: OrderedDict(x))

    with (Path(__file__).resolve().parent / 'a1dbd23261c3_wcf.json').open() as f:
        wcf_data = load(f, object_pairs_hook=lambda x: OrderedDict(x))

    with (Path(__file__).resolve().parent / f'{revision}_wsc.json').open() as f:
        wsc_data = load(f, object_pairs_hook=lambda x: OrderedDict(x))

    with (Path(__file__).resolve().parent / f'{revision}_wlc.json').open() as f:
        wlc_data = load(f, object_pairs_hook=lambda x: OrderedDict(x))

    with (Path(__file__).resolve().parent / f'{revision}_hc.json').open() as f:
        hc_data = load(f, object_pairs_hook=lambda x: OrderedDict(x))

    lbcf_chapters, lbcf_paragraphs = _get_paragraph_records(1, lbcf_data)
    wcf_chapters, wcf_paragraphs = _get_paragraph_records(2, wcf_data)

    op.bulk_insert(chapters, lbcf_chapters + wcf_chapters)
    op.bulk_insert(paragraphs, lbcf_paragraphs + wcf_paragraphs)
    op.bulk_insert(qas, _get_qa_records(3, wsc_data))
    op.bulk_insert(qas, _get_qa_records(4, wlc_data))
    op.bulk_insert(qas, _get_qa_records(5, hc_data))


def downgrade():
    op.drop_table('confess_qas')
    op.drop_table('confess_paragraphs')
    op.drop_table('confess_chapters')
    op.drop_table('confesses')
    op.drop_table('confess_types')

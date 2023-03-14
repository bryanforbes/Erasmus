"""Add Keach

Revision ID: 53ed37276d53
Revises: cbef96b83a96
Create Date: 2017-10-21 12:50:07.872595

"""
from __future__ import annotations

from json import load
from pathlib import Path
from typing import Any, Dict, List
from typing_extensions import TypedDict

import sqlalchemy as sa  # type: ignore
from alembic import op  # type: ignore
from sqlalchemy.sql import column, table  # type: ignore

# revision identifiers, used by Alembic.
revision = '53ed37276d53'
down_revision = 'cbef96b83a96'
branch_labels = None
depends_on = None

with (Path(__file__).resolve().parent / f'{revision}_keach.json').open() as f:
    keach_data = load(f)


class QAJSON(TypedDict):
    title: str
    questions: List[List[str]]


def _get_qa_records(id: str, data: QAJSON) -> List[Dict[str, Any]]:
    qas = []  # type: List[Dict[str, Any]]

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


confessions = table(
    'confessions',
    column('id', sa.Integer),
    column('command', sa.String),
    column('name', sa.String),
    column('type_id', sa.Integer, sa.ForeignKey('confession_types.id')),
    column('numbering_id', sa.Integer, sa.ForeignKey('confession_numbering_types.id')),
)

questions = table(
    'confession_questions',
    column('id', sa.Integer),
    column('confess_id', sa.Integer, sa.ForeignKey('confessions.id')),
    column('question_number', sa.Integer),
    column('question_text', sa.Text),
    column('answer_text', sa.Text),
)


def upgrade():
    op.bulk_insert(
        confessions,
        [
            {
                'id': 8,
                'command': 'keach',
                'type_id': 3,
                'numbering_id': 1,
                'name': 'Keach\'s Catechism',
            }
        ],
    )
    op.bulk_insert(questions, _get_qa_records(8, keach_data))


def downgrade():
    conn = op.get_bind()
    conn.execute(questions.delete().where(questions.c.confess_id == 8))
    conn.execute(confessions.delete().where(confessions.c.id == 8))

"""Switch to real enums for confession columns

Revision ID: a882aec7c9e4
Revises: 830329e85f73
Create Date: 2022-08-25 09:45:46.450232

"""
from typing import TypedDict

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = 'a882aec7c9e4'
down_revision = '830329e85f73'
branch_labels = None
depends_on = None

metadata = sa.MetaData()

confession_types = sa.Table(
    'confession_types',
    metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('value', sa.String(20), unique=True, nullable=False),
)

confession_numbering_types = sa.Table(
    'confession_numbering_types',
    metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('numbering', sa.String(20), unique=True, nullable=False),
)

confessions = sa.Table(
    'confessions',
    metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('command', sa.String, unique=True),
    sa.Column('name', sa.String),
    sa.Column(
        'type_id',
        sa.Integer(),
        autoincrement=False,
        nullable=False,
    ),
    sa.Column(
        'numbering_id',
        sa.Integer(),
        autoincrement=False,
        nullable=False,
    ),
    sa.Column(
        'type',
        postgresql.ENUM('ARTICLES', 'CHAPTERS', 'QA', name='confession_type'),
        nullable=False,
    ),
    sa.Column(
        'numbering',
        postgresql.ENUM('ARABIC', 'ROMAN', name='confession_numbering_type'),
        nullable=False,
    ),
)


def upgrade():
    conn = op.get_bind()

    op.execute("CREATE TYPE confession_type AS ENUM ('ARTICLES', 'CHAPTERS', 'QA')")
    op.execute("CREATE TYPE confession_numbering_type AS ENUM ('ARABIC', 'ROMAN')")

    op.add_column(
        'confessions',
        sa.Column(
            'type',
            postgresql.ENUM('ARTICLES', 'CHAPTERS', 'QA', name='confession_type'),
        ),
    )

    op.add_column(
        'confessions',
        sa.Column(
            'numbering',
            postgresql.ENUM('ARABIC', 'ROMAN', name='confession_numbering_type'),
        ),
    )

    # convert type_id to type
    result = conn.execute(confession_types.select())
    rows = result.fetchall()

    for row in rows:
        conn.execute(
            confessions.update()
            .where(confessions.c.type_id == row['id'])
            .values({'type': row['value']})
        )

    # convert numbering_id to numbering
    result = conn.execute(confession_numbering_types.select())
    rows = result.fetchall()

    for row in rows:
        conn.execute(
            confessions.update()
            .where(confessions.c.numbering_id == row['id'])
            .values({'numbering': row['numbering']})
        )

    op.alter_column('confessions', 'type', nullable=False)
    op.alter_column('confessions', 'numbering', nullable=False)

    op.drop_constraint(
        'confessions_numbering_id_fkey', 'confessions', type_='foreignkey'
    )
    op.drop_constraint('confessions_type_id_fkey', 'confessions', type_='foreignkey')
    op.drop_column('confessions', 'numbering_id')
    op.drop_column('confessions', 'type_id')
    op.drop_table('confession_numbering_types')
    op.drop_table('confession_types')


class ConfessionTypeDict(TypedDict):
    id: int
    value: str


class NumberingTypeDict(TypedDict):
    id: int
    numbering: str


def downgrade():
    conn = op.get_bind()

    confession_type_dicts: list[ConfessionTypeDict] = [
        {'id': 1, 'value': 'ARTICLES'},
        {'id': 2, 'value': 'CHAPTERS'},
        {'id': 3, 'value': 'QA'},
    ]

    numbering_type_dicts: list[NumberingTypeDict] = [
        {'id': 1, 'numbering': 'ARABIC'},
        {'id': 2, 'numbering': 'ROMAN'},
    ]

    op.create_table(
        'confession_types',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('value', sa.VARCHAR(length=20), autoincrement=False, nullable=False),
        sa.PrimaryKeyConstraint('id', name='confession_types_pkey'),
        sa.UniqueConstraint('value', name='confession_types_value_key'),
    )

    op.bulk_insert(confession_types, confession_type_dicts)

    op.create_table(
        'confession_numbering_types',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column(
            'numbering', sa.VARCHAR(length=20), autoincrement=False, nullable=False
        ),
        sa.PrimaryKeyConstraint('id', name='confession_numbering_types_pkey'),
        sa.UniqueConstraint(
            'numbering', name='confession_numbering_types_numbering_key'
        ),
    )

    op.bulk_insert(confession_numbering_types, numbering_type_dicts)

    op.add_column(
        'confessions',
        sa.Column('type_id', sa.INTEGER(), autoincrement=False),
    )
    op.add_column(
        'confessions',
        sa.Column('numbering_id', sa.INTEGER(), autoincrement=False),
    )

    # convert type to type_id and numbering to numbering_id
    for confession_type in confession_type_dicts:
        conn.execute(
            confessions.update()
            .where(confessions.c.type == confession_type['value'])
            .values({'type_id': confession_type['id']})
        )

    for numbering_type in numbering_type_dicts:
        conn.execute(
            confessions.update()
            .where(confessions.c.numbering == numbering_type['numbering'])
            .values({'numbering_id': numbering_type['id']})
        )

    op.alter_column('confessions', 'type_id', nullable=False)
    op.alter_column('confessions', 'numbering_id', nullable=False)

    op.create_foreign_key(
        'confessions_type_id_fkey',
        'confessions',
        'confession_types',
        ['type_id'],
        ['id'],
    )
    op.create_foreign_key(
        'confessions_numbering_id_fkey',
        'confessions',
        'confession_numbering_types',
        ['numbering_id'],
        ['id'],
    )

    op.drop_column('confessions', 'numbering')
    op.drop_column('confessions', 'type')

    op.execute("DROP TYPE confession_numbering_type")
    op.execute("DROP TYPE confession_type")

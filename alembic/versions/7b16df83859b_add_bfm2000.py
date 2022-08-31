"""Add BFM2000

Revision ID: 7b16df83859b
Revises: 1f333584607a
Create Date: 2022-08-29 17:05:14.518278

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = '7b16df83859b'
down_revision = '1f333584607a'
branch_labels = None
depends_on = None


def upgrade():
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE confession_numbering_type ADD VALUE 'ALPHA'")

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


def downgrade():
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

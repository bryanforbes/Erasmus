"""Add search index

Revision ID: 48f1f9cd0bee
Revises: 3a2b71b2a647
Create Date: 2023-07-26 17:11:15.382582

"""
from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = '48f1f9cd0bee'
down_revision = '3a2b71b2a647'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        'confession_sections_search_idx',
        'confession_sections',
        ['search_vector'],
        unique=False,
        postgresql_using='gin',
    )


def downgrade():
    op.drop_index(
        'confession_sections_search_idx',
        table_name='confession_sections',
        postgresql_using='gin',
    )

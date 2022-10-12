"""Add index to paragraph text

Revision ID: ac322afa9c4d
Revises: fafb6b454c85
Create Date: 2017-10-12 21:56:25.233031

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'ac322afa9c4d'
down_revision = 'fafb6b454c85'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        'confession_paragraphs_text_idx',
        'confession_paragraphs',
        [sa.text("to_tsvector('english', text)")],
        postgresql_using='gin',
    )


def downgrade():
    op.drop_index('confession_paragraphs_text_idx', 'confession_paragraphs')

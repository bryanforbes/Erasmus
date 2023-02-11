"""Add column with Markdown links stripped

Revision ID: d3f6ea0ed816
Revises: ffc7403e056d
Create Date: 2023-02-01 17:49:14.032159

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd3f6ea0ed816'
down_revision = 'ffc7403e056d'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'confession_sections',
        sa.Column(
            'text_stripped',
            sa.Text(),
            sa.Computed(
                r"regexp_replace(text, '\[(.*?)\]\(.*?\)', '\1', 'g')",
            ),
            nullable=False,
        ),
    )
    op.drop_column('confession_sections', 'search_vector')
    op.add_column(
        'confession_sections',
        sa.Column(
            'search_vector',
            postgresql.TSVECTOR(),
            sa.Computed(
                "to_tsvector('english', trim(CAST(coalesce(title, '') AS TEXT) || "
                r"' ' || CAST(regexp_replace(text, '\[(.*?)\]\(.*?\)', '\1', 'g')"
                "AS TEXT), ' '))",
            ),
            nullable=False,
        ),
    )


def downgrade():
    op.drop_column('confession_sections', 'search_vector')
    op.add_column(
        'confession_sections',
        sa.Column(
            'search_vector',
            postgresql.TSVECTOR(),
            sa.Computed(
                "to_tsvector('english', trim(coalesce(title, '') || ' ' || text, ' '))",
            ),
            nullable=True,
        ),
    )
    op.drop_column('confession_sections', 'text_stripped')

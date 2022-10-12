"""Add sortable name column

Revision ID: 830329e85f73
Revises: 8e53393e0901
Create Date: 2022-08-22 10:08:04.032643

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '830329e85f73'
down_revision = '8e53393e0901'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'confessions',
        sa.Column(
            'sortable_name',
            sa.String(),
            sa.Computed(
                "regexp_replace(name, '^(the|an?)\\s+(.*)$', '\\2, \\1', 'i')",
            ),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column('confessions', 'sortable_name')

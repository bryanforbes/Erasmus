"""Make some columns not nullable

Revision ID: dc5428c022bd
Revises: 53ed37276d53
Create Date: 2019-01-19 22:54:19.528454

"""
from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = 'dc5428c022bd'
down_revision = '53ed37276d53'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('bible_versions', 'command', nullable=False)
    op.alter_column('bible_versions', 'name', nullable=False)
    op.alter_column('bible_versions', 'abbr', nullable=False)
    op.alter_column('bible_versions', 'service', nullable=False)
    op.alter_column('bible_versions', 'service_version', nullable=False)


def downgrade():
    op.alter_column('bible_versions', 'command', nullable=True)
    op.alter_column('bible_versions', 'name', nullable=True)
    op.alter_column('bible_versions', 'abbr', nullable=True)
    op.alter_column('bible_versions', 'service', nullable=True)
    op.alter_column('bible_versions', 'service_version', nullable=True)

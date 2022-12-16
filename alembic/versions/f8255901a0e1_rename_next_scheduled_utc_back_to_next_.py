"""Rename next_scheduled_utc back to next_scheduled

Revision ID: f8255901a0e1
Revises: 8c6ef490353b
Create Date: 2022-12-16 14:14:53.440232

"""
from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = 'f8255901a0e1'
down_revision = '8c6ef490353b'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        'daily_breads', 'next_scheduled_utc', new_column_name='next_scheduled'
    )


def downgrade():
    op.alter_column(
        'daily_breads', 'next_scheduled', new_column_name='next_scheduled_utc'
    )

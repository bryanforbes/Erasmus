"""Add rtl column

Revision ID: 7cdaa5513f2d
Revises: 499dad92327d
Create Date: 2017-10-06 17:12:09.806691

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '7cdaa5513f2d'
down_revision = '499dad92327d'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('bible_versions', sa.Column('rtl', sa.Boolean, default=False))


def downgrade():
    op.drop_column('bible_versions', 'rtl')

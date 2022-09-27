"""Add verse of the day table

Revision ID: d21c001d987c
Revises: 300fb8300fb7
Create Date: 2022-09-26 09:09:00.714696

"""
import sqlalchemy as sa
from botus_receptus.sqlalchemy import Snowflake
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = 'd21c001d987c'
down_revision = '300fb8300fb7'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'guild_votd',
        sa.Column('guild_id', Snowflake(), nullable=False),
        sa.Column('channel_id', Snowflake(), nullable=False),
        sa.Column('thread_id', Snowflake(), nullable=True),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column(
            'next_scheduled', postgresql.TIMESTAMP(timezone=True), nullable=False
        ),
        sa.PrimaryKeyConstraint('guild_id'),
    )


def downgrade():
    op.drop_table('guild_votd')

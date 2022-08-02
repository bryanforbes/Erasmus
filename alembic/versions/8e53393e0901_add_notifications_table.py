"""Add notifications table

Revision ID: 8e53393e0901
Revises: f343a13c8b35
Create Date: 2022-08-02 09:35:18.810107

"""
import sqlalchemy as sa
from botus_receptus.sqlalchemy import Snowflake

from alembic import op

# revision identifiers, used by Alembic.
revision = '8e53393e0901'
down_revision = 'f343a13c8b35'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'notifications',
        sa.Column('id', Snowflake(), nullable=False),
        sa.Column('application_commands', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('notifications')
    # ### end Alembic commands ###

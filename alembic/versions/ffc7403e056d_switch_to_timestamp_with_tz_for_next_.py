"""Switch to timestamp with tz for next_scheduled

Revision ID: ffc7403e056d
Revises: f8255901a0e1
Create Date: 2023-01-24 11:55:30.262771

"""
from __future__ import annotations

import datetime

import sqlalchemy as sa
from alembic import op
from botus_receptus.sqlalchemy import Snowflake
from sqlalchemy.dialects.postgresql import TIMESTAMP

# revision identifiers, used by Alembic.
revision = 'ffc7403e056d'
down_revision = 'f8255901a0e1'
branch_labels = None
depends_on = None

daily_breads_before = sa.table(
    'daily_breads',
    sa.column('guild_id', Snowflake()),
    sa.column('next_scheduled', TIMESTAMP(timezone=False)),
)
daily_breads_after = sa.table(
    'daily_breads',
    sa.column('guild_id', Snowflake()),
    sa.column('next_scheduled', TIMESTAMP(timezone=True)),
)


def upgrade():
    conn = op.get_bind()

    result = conn.execute(daily_breads_before.select())
    rows = result.fetchall()

    op.alter_column(
        'daily_breads',
        'next_scheduled',
        type_=TIMESTAMP(timezone=True),
    )

    for row in rows:
        op.execute(
            daily_breads_after.update()
            .filter_by(guild_id=row[0])
            .values({'next_scheduled': row[1].replace(tzinfo=datetime.timezone.utc)})
        )


def downgrade():
    conn = op.get_bind()

    result = conn.execute(daily_breads_after.select())
    rows = result.fetchall()

    op.alter_column(
        'daily_breads',
        'next_scheduled',
        type_=TIMESTAMP(timezone=False),
    )

    for row in rows:
        op.execute(
            daily_breads_before.update()
            .filter_by(guild_id=row[0])
            .values({'next_scheduled': row[1].naive()})
        )

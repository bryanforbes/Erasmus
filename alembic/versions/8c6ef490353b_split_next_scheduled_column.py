"""Split next_scheduled column

Revision ID: 8c6ef490353b
Revises: e5249c54cbcd
Create Date: 2022-10-24 16:50:07.223883

"""
from __future__ import annotations

import pendulum
import sqlalchemy as sa
from alembic import op
from botus_receptus.sqlalchemy import Snowflake

from erasmus.db.types import DateTime, Time, Timezone

# revision identifiers, used by Alembic.
revision = '8c6ef490353b'
down_revision = 'e5249c54cbcd'
branch_labels = None
depends_on = None

daily_breads_before = sa.table(
    'daily_breads',
    sa.column('guild_id', Snowflake()),
    sa.column('next_scheduled', DateTime(timezone=True)),
)
daily_breads_after = sa.table(
    'daily_breads',
    sa.column('guild_id', Snowflake()),
    sa.column('next_scheduled', DateTime(timezone=False)),
    sa.column('time', Time()),
    sa.column('timezone', Timezone()),
)


def upgrade():
    conn = op.get_bind()

    local_tz = pendulum.local_timezone()
    result = conn.execute(daily_breads_before.select())
    rows = result.fetchall()

    op.alter_column(
        'daily_breads',
        'next_scheduled',
        type_=DateTime(timezone=False),
    )
    op.add_column('daily_breads', sa.Column('time', Time(), nullable=True))
    op.add_column('daily_breads', sa.Column('timezone', Timezone(), nullable=True))

    for row in rows:
        op.execute(
            daily_breads_after.update()
            .filter_by(guild_id=row[0])
            .values(
                {
                    'next_scheduled': row[1].astimezone(pendulum.UTC),
                    'time': row[1].astimezone(local_tz).time(),
                    'timezone': local_tz,
                }
            )
        )

    op.alter_column('daily_breads', 'time', nullable=False)
    op.alter_column('daily_breads', 'timezone', nullable=False)


def downgrade():
    conn = op.get_bind()

    result = conn.execute(daily_breads_after.select())
    rows = result.fetchall()

    op.drop_column('daily_breads', 'timezone')
    op.drop_column('daily_breads', 'time')
    op.alter_column(
        'daily_breads',
        'next_scheduled',
        type_=DateTime(timezone=True),
    )

    for row in rows:
        op.execute(
            daily_breads_before.update()
            .filter_by(guild_id=row[0])
            .values({'next_scheduled': row[1].astimezone(row[3])})
        )

"""Fix Westminster naming

Revision ID: 2b3acfa18257
Revises: d3f6ea0ed816
Create Date: 2023-07-24 13:36:06.876058

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '2b3acfa18257'
down_revision = 'd3f6ea0ed816'
branch_labels = None
depends_on = None

confessions = sa.table(
    'confessions',
    sa.column('command', sa.String),
    sa.column('name', sa.String),
)


def upgrade():
    op.execute(
        confessions.update()
        .filter(confessions.c.command == 'wsc')
        .values(name='The Westminster Shorter Catechism')
    )
    op.execute(
        confessions.update()
        .filter(confessions.c.command == 'wlc')
        .values(name='The Westminster Larger Catechism')
    )


def downgrade():
    op.execute(
        confessions.update()
        .filter(confessions.c.command == 'wlc')
        .values(name='The Wesminster Longer Catechism')
    )
    op.execute(
        confessions.update()
        .filter(confessions.c.command == 'wsc')
        .values(name='The Wesminster Shorter Catechism')
    )

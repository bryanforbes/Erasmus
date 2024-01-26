"""Add book mapping, fix LXX, and add sortable name for Bibles

Revision ID: 902fb954c12f
Revises: 2f3c14b064be
Create Date: 2022-09-23 12:58:13.299222

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '902fb954c12f'
down_revision = '2f3c14b064be'
branch_labels = None
depends_on = None


bible_versions = sa.table(
    'bible_versions',
    sa.column('id', sa.Integer),
    sa.column('command', sa.String),
    sa.column('name', sa.String),
    sa.column('abbr', sa.String),
    sa.column('service', sa.String),
    sa.column('service_version', sa.String),
    sa.column('rtl', sa.Boolean),
    sa.column('books', sa.BigInteger),
    sa.column(
        'book_mapping', postgresql.JSONB(none_as_null=True, astext_type=sa.Text())
    ),
)


def upgrade():
    op.add_column(
        'bible_versions',
        sa.Column(
            'book_mapping',
            postgresql.JSONB(none_as_null=True, astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column(
        'bible_versions',
        sa.Column(
            'sortable_name',
            sa.String(),
            sa.Computed(
                "regexp_replace(name, '^(the|an?)\\s+(.*)$', '\\2, \\1', 'i')",
            ),
            nullable=True,
        ),
    )
    op.create_index(
        'bible_versions_sortable_name_order_idx',
        'bible_versions',
        [sa.text('sortable_name ASC')],
        unique=False,
    )
    op.execute(
        bible_versions.update()
        .filter(bible_versions.c.command == 'lxx')
        .values(
            {
                'name': 'Septuagint (Brenton)',
                'service': 'ApiBible',
                'service_version': 'c114c33098c4fef1-01',
                'books': 4784381,
                'book_mapping': {'Dan': 'DanGr', 'Esth': 'EsthGr'},
            }
        )
    )


def downgrade():
    op.execute(
        bible_versions.update()
        .filter(bible_versions.c.command == 'lxx')
        .values(
            {
                'name': 'Septuaginta, ed. A. Rahlfs',
                'service': 'Unbound',
                'service_version': 'lxx_a_accents_ucs2',
                'books': 4062975,
            }
        )
    )
    op.drop_index('bible_versions_sortable_name_order_idx', table_name='bible_versions')
    op.drop_column('bible_versions', 'sortable_name')
    op.drop_column('bible_versions', 'book_mapping')

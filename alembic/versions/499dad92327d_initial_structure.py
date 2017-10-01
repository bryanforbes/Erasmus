"""initial structure

Revision ID: 499dad92327d
Revises: 
Create Date: 2017-09-30 21:47:58.501740

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '499dad92327d'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    bible_versions = op.create_table('bible_versions',
                                     sa.Column('id', sa.Integer, primary_key=True),
                                     sa.Column('command', sa.String, unique=True),
                                     sa.Column('name', sa.String),
                                     sa.Column('abbr', sa.String),
                                     sa.Column('service', sa.String),
                                     sa.Column('service_version', sa.String))

    op.create_table('guild_bibles',
                    sa.Column('guild_id', sa.String, primary_key=True),
                    sa.Column('bible_id', sa.Integer,
                              sa.ForeignKey('bible_versions.id'), primary_key=True))

    op.create_table('guild_prefs',
                    sa.Column('guild_id', sa.String, primary_key=True),
                    sa.Column('prefix', sa.String(1), default='$'))

    op.bulk_insert(bible_versions, [
        dict(command='esv', name='English Standard Version', abbr='ESV',
             service='BiblesOrg', service_version='eng-ESV'),
        dict(command='kjv', name='King James Version', abbr='KJV',
             service='BiblesOrg', service_version='eng-KJV'),
        dict(command='kjva', name='King James Version with Apocrypha', abbr='KJV w/ Apocrypha',
             service='BiblesOrg', service_version='eng-KJVA'),
        dict(command='nasb', name='New American Standard Bible', abbr='NASB',
             service='BiblesOrg', service_version='eng-NASB'),
        dict(command='sbl', name='SBL Greek New Testament', abbr='SBL GNT',
             service='BibleGateway', service_version='SBLGNT'),
        dict(command='niv', name='New International Version', abbr='NIV',
             service='BibleGateway', service_version='NIV'),
        dict(command='lxx', name='Septuaginta, ed. A. Rahlfs', abbr='LXX',
             service='Unbound', service_version='lxx_a_accents_ucs2'),
        dict(command='csb', name='Christian Standard Bible', abbr='CSB',
             service='BibleGateway', service_version='CSB'),
        dict(command='isv', name='International Standard Version', abbr='ISV',
             service='BibleGateway', service_version='ISV'),
        dict(command='net', name='New English Translation', abbr='NET',
             service='BibleGateway', service_version='NET'),
        dict(command='nrsv', name='New Revised Standard Version', abbr='NRSV',
             service='BibleGateway', service_version='NRSV'),
    ])


def downgrade():
    op.drop_table('guild_prefs')
    op.drop_table('guild_bibles')
    op.drop_table('bible_versions')

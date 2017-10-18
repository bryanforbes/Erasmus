"""Reorganize confession tables

Revision ID: cbef96b83a96
Revises: b00769d6f457
Create Date: 2017-10-16 20:33:37.695254

"""
from alembic import op  # type: ignore
import sqlalchemy as sa  # type: ignore


# revision identifiers, used by Alembic.
revision = 'cbef96b83a96'
down_revision = 'b00769d6f457'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table('confession_paragraphs')
    op.drop_table('confession_chapters')
    op.drop_table('confessions')

    op.rename_table('confess_articles', 'confession_articles')
    op.execute('ALTER TABLE confession_articles '
               'RENAME CONSTRAINT confess_articles_confess_id_fkey TO confession_articles_confess_id_fkey')
    op.execute('ALTER SEQUENCE confess_articles_id_seq RENAME TO confession_articles_id_seq')
    op.execute('ALTER INDEX confess_articles_pkey RENAME TO confession_articles_pkey')
    op.execute('ALTER INDEX confess_articles_text_idx RENAME TO confession_articles_text_idx')

    op.rename_table('confess_chapters', 'confession_chapters')
    op.execute('ALTER TABLE confession_chapters '
               'RENAME CONSTRAINT confess_chapters_confess_id_fkey TO confession_chapters_confess_id_fkey')
    op.execute('ALTER SEQUENCE confess_chapters_id_seq RENAME TO confession_chapters_id_seq')
    op.execute('ALTER INDEX confess_chapters_pkey RENAME TO confession_chapters_pkey')

    op.rename_table('confess_numbering_type', 'confession_numbering_types')
    op.execute('ALTER SEQUENCE confess_numbering_type_id_seq RENAME TO confession_numbering_types_id_seq')
    op.execute('ALTER INDEX confess_numbering_type_numbering_key RENAME TO confession_numbering_types_numbering_key')
    op.execute('ALTER INDEX confess_numbering_type_pkey RENAME TO confession_numbering_types_pkey')

    op.rename_table('confess_paragraphs', 'confession_paragraphs')
    op.execute('ALTER TABLE confession_paragraphs '
               'RENAME CONSTRAINT confess_paragraphs_confess_id_fkey TO confession_paragraphs_confess_id_fkey')
    op.execute('ALTER SEQUENCE confess_paragraphs_id_seq RENAME TO confession_paragraphs_id_seq')
    op.execute('ALTER INDEX confess_paragraphs_pkey RENAME TO confession_paragraphs_pkey')
    op.execute('ALTER INDEX confess_paragraphs_text_idx RENAME TO confession_paragraphs_text_idx')

    op.rename_table('confess_qas', 'confession_questions')
    op.execute('ALTER TABLE confession_questions '
               'RENAME CONSTRAINT confess_qas_confess_id_fkey TO confession_questions_confess_id_fkey')
    op.execute('ALTER SEQUENCE confess_qas_id_seq RENAME TO confession_questions_id_seq')
    op.execute('ALTER INDEX confess_qas_pkey RENAME TO confession_questions_pkey')
    op.execute('ALTER INDEX confess_qas_text_idx RENAME TO confession_questions_text_idx')

    op.rename_table('confess_types', 'confession_types')
    op.execute('ALTER SEQUENCE confess_types_id_seq RENAME TO confession_types_id_seq')
    op.execute('ALTER INDEX confess_types_pkey RENAME TO confession_types_pkey')
    op.execute('ALTER INDEX confess_types_value_key RENAME TO confession_types_value_key')

    op.rename_table('confesses', 'confessions')
    op.execute('ALTER TABLE confessions '
               'RENAME CONSTRAINT confesses_numbering_id_fkey TO confessions_numbering_id_fkey')
    op.execute('ALTER TABLE confessions '
               'RENAME CONSTRAINT confesses_type_id_fkey TO confessions_type_id_fkey')
    op.execute('ALTER SEQUENCE confesses_id_seq RENAME TO confessions_id_seq')
    op.execute('ALTER INDEX confesses_pkey RENAME TO confessions_pkey')
    op.execute('ALTER INDEX confesses_command_key RENAME TO confessions_command_key')


def downgrade():
    op.rename_table('confession_articles', 'confess_articles')
    op.execute('ALTER TABLE confess_articles '
               'RENAME CONSTRAINT confession_articles_confess_id_fkey TO confess_articles_confess_id_fkey')
    op.execute('ALTER SEQUENCE confession_articles_id_seq RENAME TO confess_articles_id_seq')
    op.execute('ALTER INDEX confession_articles_pkey RENAME TO confess_articles_pkey')
    op.execute('ALTER INDEX confession_articles_text_idx RENAME TO confess_articles_text_idx')

    op.rename_table('confession_chapters', 'confess_chapters')
    op.execute('ALTER TABLE confess_chapters '
               'RENAME CONSTRAINT confession_chapters_confess_id_fkey TO confess_chapters_confess_id_fkey')
    op.execute('ALTER SEQUENCE confession_chapters_id_seq RENAME TO confess_chapters_id_seq')
    op.execute('ALTER INDEX confession_chapters_pkey RENAME TO confess_chapters_pkey')

    op.rename_table('confession_numbering_types', 'confess_numbering_type')
    op.execute('ALTER SEQUENCE confession_numbering_types_id_seq RENAME TO confess_numbering_type_id_seq')
    op.execute('ALTER INDEX confession_numbering_types_numbering_key RENAME TO confess_numbering_type_numbering_key')
    op.execute('ALTER INDEX confession_numbering_types_pkey RENAME TO confess_numbering_type_pkey')

    op.rename_table('confession_paragraphs', 'confess_paragraphs')
    op.execute('ALTER TABLE confess_paragraphs '
               'RENAME CONSTRAINT confession_paragraphs_confess_id_fkey TO confess_paragraphs_confess_id_fkey')
    op.execute('ALTER SEQUENCE confession_paragraphs_id_seq RENAME TO confess_paragraphs_id_seq')
    op.execute('ALTER INDEX confession_paragraphs_pkey RENAME TO confess_paragraphs_pkey')
    op.execute('ALTER INDEX confession_paragraphs_text_idx RENAME TO confess_paragraphs_text_idx')

    op.rename_table('confession_questions', 'confess_qas')
    op.execute('ALTER TABLE confess_qas '
               'RENAME CONSTRAINT confession_questions_confess_id_fkey TO confess_qas_confess_id_fkey')
    op.execute('ALTER SEQUENCE confession_questions_id_seq RENAME TO confess_qas_id_seq')
    op.execute('ALTER INDEX confession_questions_pkey RENAME TO confess_qas_pkey')
    op.execute('ALTER INDEX confession_questions_text_idx RENAME TO confess_qas_text_idx')

    op.rename_table('confession_types', 'confess_types')
    op.execute('ALTER SEQUENCE confession_types_id_seq RENAME TO confess_types_id_seq')
    op.execute('ALTER INDEX confession_types_pkey RENAME TO confess_types_pkey')
    op.execute('ALTER INDEX confession_types_value_key RENAME TO confess_types_value_key')

    op.rename_table('confessions', 'confesses')
    op.execute('ALTER TABLE confesses '
               'RENAME CONSTRAINT confessions_numbering_id_fkey TO confesses_numbering_id_fkey')
    op.execute('ALTER TABLE confesses '
               'RENAME CONSTRAINT confessions_type_id_fkey TO confesses_type_id_fkey')
    op.execute('ALTER SEQUENCE confessions_id_seq RENAME TO confesses_id_seq')
    op.execute('ALTER INDEX confessions_pkey RENAME TO confesses_pkey')
    op.execute('ALTER INDEX confessions_command_key RENAME TO confesses_command_key')

    op.create_table('confessions',
                    sa.Column('id', sa.Integer, primary_key=True),
                    sa.Column('command', sa.String, unique=True),
                    sa.Column('name', sa.String))
    op.create_table('confession_chapters',
                    sa.Column('id', sa.Integer, primary_key=True),
                    sa.Column('confession_id', sa.Integer,
                              sa.ForeignKey('confessions.id')),
                    sa.Column('chapter_number', sa.Integer),
                    sa.Column('title', sa.String))
    op.create_table('confession_paragraphs',
                    sa.Column('id', sa.Integer, primary_key=True),
                    sa.Column('confession_id', sa.Integer,
                              sa.ForeignKey('confessions.id')),
                    sa.Column('chapter_number', sa.Integer),
                    sa.Column('paragraph_number', sa.Integer),
                    sa.Column('text', sa.Text))
    op.create_index('confession_paragraphs_text_idx', 'confession_paragraphs',
                    [sa.text("to_tsvector('english', text)")],
                    postgresql_using='gin')

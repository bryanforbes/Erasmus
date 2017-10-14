from sqlalchemy import (  # type: ignore
    MetaData, Table, Column, Integer, String, ForeignKey, Boolean, BigInteger,
    Text, Index, func, column
)
import sqlalchemy.types as types  # type: ignore
from sqlalchemy.dialects.postgresql import insert  # type: ignore

__all__ = ['insert', 'Snowflake', 'metadata', 'bible_versions', 'guild_bibles',
           'guild_prefs', 'user_prefs', 'confessions', 'confession_chapters',
           'confession_paragraphs']


class Snowflake(types.TypeDecorator):
    impl = types.String

    def process_bind_param(self, value, dialect):
        if not isinstance(value, int):
            raise TypeError(f'expected int, got {type(value).__name__}')

        return str(value)

    def process_result_value(self, value, dialect):
        return int(value)


metadata = MetaData()

bible_versions = Table('bible_versions', metadata,
                       Column('id', Integer, primary_key=True),
                       Column('command', String, unique=True),
                       Column('name', String),
                       Column('abbr', String),
                       Column('service', String),
                       Column('service_version', String),
                       Column('rtl', Boolean, default=False),
                       Column('books', BigInteger, nullable=False))

guild_bibles = Table('guild_bibles', metadata,
                     Column('guild_id', Snowflake, primary_key=True),
                     Column('bible_id', Integer, ForeignKey('bible_versions.id'), primary_key=True))

guild_prefs = Table('guild_prefs', metadata,
                    Column('guild_id', Snowflake, primary_key=True),
                    Column('prefix', String(1), default='$'))

user_prefs = Table('user_prefs', metadata,
                   Column('user_id', Snowflake, primary_key=True),
                   Column('bible_id', Integer, ForeignKey('bible_versions.id')))

confessions = Table('confessions', metadata,
                    Column('id', Integer, primary_key=True),
                    Column('command', String, unique=True),
                    Column('name', String))

confession_chapters = Table('confession_chapters', metadata,
                            Column('id', Integer, primary_key=True),
                            Column('confession_id', Integer, ForeignKey('confessions.id')),
                            Column('chapter_number', Integer),
                            Column('title', String))

confession_paragraphs = Table('confession_paragraphs', metadata,
                              Column('id', Integer, primary_key=True),
                              Column('confession_id', Integer, ForeignKey('confessions.id')),
                              Column('chapter_number', Integer),
                              Column('paragraph_number', Integer),
                              Column('text', Text),
                              Index('confession_paragraphs_text_idx',
                                    func.to_tsvector('english', column('text')),
                                    postgresql_using='gin'))

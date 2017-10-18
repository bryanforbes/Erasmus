from sqlalchemy import (  # type: ignore
    MetaData, Table, Column, Integer, String, ForeignKey, Boolean, BigInteger,
    Text, Index, func
)
import sqlalchemy.types as types  # type: ignore


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

confession_types = Table('confession_types', metadata,
                         Column('id', Integer, primary_key=True),
                         Column('value', String(20), unique=True, nullable=False))

confessions = Table('confessions', metadata,
                    Column('id', Integer, primary_key=True),
                    Column('command', String, unique=True),
                    Column('name', String, nullable=False),
                    Column('type_id', Integer,
                           ForeignKey('confession_types.id'), nullable=False),
                    Column('numbering_id', Integer,
                           ForeignKey('confession_numbering_types.id'),
                           nullable=False))

chapters = Table('confession_chapters', metadata,
                 Column('id', Integer, primary_key=True),
                 Column('confess_id', Integer,
                        ForeignKey('confessions.id'), nullable=False),
                 Column('chapter_number', Integer, nullable=False),
                 Column('chapter_title', String, nullable=False))

paragraphs = Table('confession_paragraphs', metadata,
                   Column('id', Integer, primary_key=True),
                   Column('confess_id', Integer,
                          ForeignKey('confessions.id'), nullable=False),
                   Column('chapter_number', Integer, nullable=False),
                   Column('paragraph_number', Integer, nullable=False),
                   Column('text', Text, nullable=False),
                   Index('confession_paragraphs_text_idx',
                         func.to_tsvector('english', 'text'),
                         postgresql_using='gin'))

questions = Table('confession_questions', metadata,
                  Column('id', Integer, primary_key=True),
                  Column('confess_id', Integer,
                         ForeignKey('confessions.id'), nullable=False),
                  Column('question_number', Integer, nullable=False),
                  Column('question_text', Text, nullable=False),
                  Column('answer_text', Text, nullable=False),
                  Index('confession_questions_text_idx',
                        func.to_tsvector('english', "question_text || ' ' || answer_text"),
                        postgresql_using='gin'))

numbering_types = Table('confession_numbering_types', metadata,
                        Column('id', Integer, primary_key=True),
                        Column('numbering', String(20), unique=True, nullable=False))

articles = Table('confession_articles', metadata,
                 Column('id', Integer, primary_key=True),
                 Column('confess_id', Integer,
                        ForeignKey('confessions.id'), nullable=False),
                 Column('article_number', Integer, nullable=False),
                 Column('title', String, nullable=False),
                 Column('text', Text, nullable=False),
                 Index('confession_articles_text_idx',
                       func.to_tsvector('english', 'text'),
                       postgresql_using='gin'))

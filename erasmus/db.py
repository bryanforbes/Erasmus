from sqlalchemy import MetaData, Table, Column, Integer, String, ForeignKey  # type: ignore
import sqlalchemy.types as types  # type: ignore
from sqlalchemy.dialects.postgresql import insert  # type: ignore

__all__ = ['insert', 'Snowflake', 'metadata', 'bible_versions', 'guild_bibles',
           'guild_prefs', 'user_prefs']


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
                       Column('service_version', String))

guild_bibles = Table('guild_bibles', metadata,
                     Column('guild_id', Snowflake, primary_key=True),
                     Column('bible_id', Integer, ForeignKey('bible_versions.id'), primary_key=True))

guild_prefs = Table('guild_prefs', metadata,
                    Column('guild_id', Snowflake, primary_key=True),
                    Column('prefix', String(1), default='$'))

user_prefs = Table('user_prefs', metadata,
                   Column('user_id', Snowflake, primary_key=True),
                   Column('bible_id', Integer, ForeignKey('bible_versions.id')))

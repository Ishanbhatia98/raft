import os
import urllib.parse

from sqlalchemy.engine import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeMeta, Session, sessionmaker


class DatabaseInstance:
    _base: DeclarativeMeta = None

    def __init__(self):
        self._base = declarative_base()
        self._engine = create_engine(
            self.get_database_url(),
            max_overflow=20,
            pool_recycle=3600,
            pool_size=2,
        )
        self._session_maker = sessionmaker(autocommit=False, bind=self._engine)

    @property
    def base(self) -> DeclarativeMeta:
        return self._base

    @staticmethod
    def get_database_url() -> str:
        db_name = os.getenv("POSTGRES_DB")
        db_host = os.getenv("POSTGRES_HOST")
        db_port = os.getenv("POSTGRES_PORT")
        db_ssl_mode = os.getenv("POSTGRES_SSLMODE", "prefer")

        db_user = urllib.parse.quote(os.getenv("POSTGRES_USER"))
        db_password = urllib.parse.quote(os.getenv("POSTGRES_PASSWORD"))

        return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?sslmode={db_ssl_mode}"

    def initialize_session(self) -> Session:
        return self._session_maker()

    def delete_all_tables_and_metadata(self):
        # Get a session from the session maker
        session = self.initialize_session()

        # Reflect all tables and drop the entire schema
        self.base.metadata.drop_all(self._engine)

        # Commit the changes and close the session
        session.commit()
        session.close()


db_instance = DatabaseInstance()

def get_db_session():
    if hasattr(get_db_session, "_session") and not get_db_session._session.is_active:
        return get_db_session._session
    session = db_instance.initialize_session()
    get_db_session._session = session
    return session


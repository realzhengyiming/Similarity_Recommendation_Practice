from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import NullPool

from config import config


class DataSession(object):
    config = config
    psql_uri = config.PSQL_URI
    session = None

    def get_session(self):
        if self.session is None:
            db_engine = create_engine(self.psql_uri, poolclass=NullPool)
            DBSession = sessionmaker(bind=db_engine, autoflush=False)
            Session = scoped_session(DBSession)
            self.session = Session
        return self.session

    def get_engine(self):
        db_engine = create_engine(self.psql_uri)
        return db_engine


data_session_instance = DataSession()

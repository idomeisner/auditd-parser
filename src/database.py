from sqlalchemy import create_engine
from sqlalchemy.exc import ArgumentError, OperationalError
from sqlalchemy.orm import sessionmaker

from config import get_logger
from models import Base

logger = get_logger()


class Database:
    """
    Database Singleton
    """

    _instance = None

    def __new__(cls, db_url: str):
        if not cls._instance:
            try:
                cls._instance = super().__new__(cls)
                cls._instance._initialize(db_url)
            except (OperationalError, ArgumentError) as e:
                logger.error(f"Failed to connect to {db_url!r} database, {e=}")
                raise

        return cls._instance

    def _initialize(self, db_url):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)

    def get_session(self):
        return sessionmaker(bind=self.engine)

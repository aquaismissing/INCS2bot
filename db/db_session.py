import logging
from pathlib import Path

from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker

SqlAlchemyBase = declarative_base()

_factory: async_sessionmaker | None = None


def global_init(db_file: Path):
    global _factory

    if _factory:
        return

    conn_str = f'sqlite+aiosqlite:///{db_file}?check_same_thread=False'
    logging.info(f'Connecting to database in {conn_str}')

    engine = create_async_engine(conn_str, echo=False)
    _factory = async_sessionmaker(bind=engine)

    from . import __all_models

    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    global _factory

    return _factory()

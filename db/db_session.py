import logging
from pathlib import Path

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncSession, async_sessionmaker, create_async_engine


logger = logging.getLogger('INCS2bot.db')


class SqlAlchemyBase(AsyncAttrs, DeclarativeBase):
    pass


_factory: async_sessionmaker | None = None


async def init(db_file: Path):
    global _factory

    if _factory:
        return

    conn_str = f'sqlite+aiosqlite:///{db_file}?check_same_thread=False'
    logger.info(f'Connecting to database in {conn_str}')

    engine = create_async_engine(conn_str, echo=False)

    # noinspection PyUnresolvedReferences
    from . import __all_models

    async with engine.begin() as conn:
        await conn.run_sync(SqlAlchemyBase.metadata.create_all)

    _factory = async_sessionmaker(bind=engine, expire_on_commit=False)


def create_session() -> AsyncSession:
    return _factory()

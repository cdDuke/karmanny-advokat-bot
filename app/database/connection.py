from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.models import Base


def create_session_factory(database_url: str) -> tuple[async_sessionmaker[AsyncSession], AsyncEngine]:
    engine = create_async_engine(database_url, pool_pre_ping=True)

    if database_url.startswith("sqlite"):
        @event.listens_for(engine.sync_engine, "connect")
        def enable_sqlite_foreign_keys(dbapi_connection, connection_record) -> None:  # type: ignore[no-untyped-def]
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return async_sessionmaker(engine, expire_on_commit=False), engine


async def init_db(engine: AsyncEngine) -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        await _ensure_sqlite_user_columns(connection)


async def _ensure_sqlite_user_columns(connection) -> None:  # type: ignore[no-untyped-def]
    dialect_name = connection.dialect.name
    if dialect_name != "sqlite":
        return

    result = await connection.exec_driver_sql("PRAGMA table_info(users)")
    columns = {row[1] for row in result.fetchall()}
    required = {
        "telegram_id": "ALTER TABLE users ADD COLUMN telegram_id BIGINT",
        "country_code": "ALTER TABLE users ADD COLUMN country_code VARCHAR(2)",
        "requests_count": "ALTER TABLE users ADD COLUMN requests_count INTEGER NOT NULL DEFAULT 0",
        "documents_count": "ALTER TABLE users ADD COLUMN documents_count INTEGER NOT NULL DEFAULT 0",
    }
    for column, statement in required.items():
        if column not in columns:
            await connection.exec_driver_sql(statement)


@asynccontextmanager
async def session_scope(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

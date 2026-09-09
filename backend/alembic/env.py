from logging.config import fileConfig
import asyncio
from alembic import context
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy.pool import NullPool
from app.core.config import settings
from app.db.base import Base
from app.db import models  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)
if config.config_file_name:
    fileConfig(config.config_file_name)
target_metadata = Base.metadata

def run_migrations_offline():
    context.configure(url=settings.database_url.replace("+asyncpg",""),
                      target_metadata=target_metadata, literal_binds=True,
                      dialect_opts={"paramstyle":"named"})
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations():
    engine = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.", poolclass=NullPool)
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()

def run_migrations_online():
    asyncio.run(run_async_migrations())

run_migrations_offline() if context.is_offline_mode() else run_migrations_online()

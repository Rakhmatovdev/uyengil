import asyncio
import os
from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine
from app.database.base import Base
from app.database import models  # noqa: F401
from app.database.session import normalize_database_url


def migrate(connection):
    context.configure(connection=connection, target_metadata=Base.metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run():
    from dotenv import load_dotenv
    load_dotenv()
    engine = create_async_engine(normalize_database_url(os.environ['DATABASE_URL']))
    async with engine.connect() as connection:
        await connection.run_sync(migrate)
    await engine.dispose()


asyncio.run(run())

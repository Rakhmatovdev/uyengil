import os
import pytest_asyncio
from app.database.base import Base, utcnow
from app.database.models import User, Order
from app.database.session import create_database
from datetime import timedelta
from decimal import Decimal


@pytest_asyncio.fixture
async def db(tmp_path):
    # TEST_DATABASE_URL must point to a dedicated disposable PostgreSQL database.
    url = os.getenv('TEST_DATABASE_URL', f'sqlite+aiosqlite:///{tmp_path / "test.db"}')
    engine, sessions = create_database(url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with sessions.begin() as session:
        users = [User(telegram_id=i, username=f'user{i}', first_name=f'User {i}') for i in range(1, 4)]
        session.add_all(users)
        await session.flush()
        order = Order(user_id=users[0].id, type='SELL', amount=Decimal('500'), creation_key='test-order',
            expires_at=utcnow() + timedelta(hours=24))
        session.add(order)
        await session.flush()
    yield sessions, users, order
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
    await engine.dispose()

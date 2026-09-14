import asyncio
import os
from datetime import timedelta
import pytest
from sqlalchemy import select, func
from app.database.base import utcnow
from app.database.models import Match, Order, Notification
from app.services.match_service import MatchService
from app.services.order_service import DomainError, OrderService, parse_amount


@pytest.mark.parametrize('value', ['0', '-1', 'NaN', 'Infinity', '1e3', '1.001', '100000001', '<b>1</b>'])
def test_invalid_amount(value):
    with pytest.raises(DomainError):
        parse_amount(value)


def test_decimal_amount():
    assert str(parse_amount('500,50')) == '500.50'


async def test_two_confirmations_and_idempotency(db):
    sessions, users, order = db
    service = MatchService(sessions)
    match = await service.reserve(order.id, users[1])
    await service.decide(match.id, users[1].id, True)
    async with sessions() as session:
        assert (await session.get(Order, order.id)).status == 'RESERVED'
        assert await session.scalar(select(func.count()).select_from(Notification)) == 2
    await service.decide(match.id, users[0].id, True)
    await service.decide(match.id, users[0].id, True)
    async with sessions() as session:
        assert (await session.get(Order, order.id)).status == 'MATCHED'
        assert await session.scalar(select(func.count()).select_from(Notification)) == 4


async def test_self_reservation_and_third_party_denied(db):
    sessions, users, order = db
    service = MatchService(sessions)
    with pytest.raises(DomainError):
        await service.reserve(order.id, users[0])
    match = await service.reserve(order.id, users[1])
    with pytest.raises(DomainError):
        await service.reserve(order.id, users[2])
    with pytest.raises(DomainError):
        await service.decide(match.id, users[2].id, True)


async def test_timeout_stale_button_cannot_confirm_new_match(db):
    sessions, users, order = db
    service = MatchService(sessions)
    old = await service.reserve(order.id, users[1])
    async with sessions.begin() as session:
        (await session.get(Match, old.id)).expires_at = utcnow() - timedelta(seconds=1)
    await OrderService(sessions).cleanup()
    new = await service.reserve(order.id, users[2])
    result = await service.decide(old.id, users[0].id, True)
    assert 'tugagan' in result
    async with sessions() as session:
        assert (await session.get(Match, old.id)).status == 'EXPIRED'
        assert not (await session.get(Match, new.id)).seller_confirmed


async def test_cancel_reservation_and_owner_cancel(db):
    sessions, users, order = db
    service = MatchService(sessions)
    match = await service.reserve(order.id, users[1])
    await service.decide(match.id, users[0].id, False)
    with pytest.raises(DomainError):
        await OrderService(sessions).cancel(order.id, users[2].id)
    await OrderService(sessions).cancel(order.id, users[0].id)
    async with sessions() as session:
        assert (await session.get(Order, order.id)).status == 'CANCELLED'


async def test_buy_order_roles(db):
    sessions, users, order = db
    async with sessions.begin() as session:
        (await session.get(Order, order.id)).type = 'BUY'
    match = await MatchService(sessions).reserve(order.id, users[1])
    assert match.buyer_id == users[0].id
    assert match.seller_id == users[1].id


async def test_expired_order_hidden(db):
    sessions, users, order = db
    async with sessions.begin() as session:
        (await session.get(Order, order.id)).expires_at = utcnow() - timedelta(seconds=1)
    assert await OrderService(sessions).list(users[1].id) == []


@pytest.mark.skipif(not os.getenv('TEST_DATABASE_URL', '').startswith('postgresql'), reason='Requires PostgreSQL row locks')
async def test_concurrent_reservation_only_one_winner(db):
    sessions, users, order = db
    service = MatchService(sessions)
    results = await asyncio.gather(service.reserve(order.id, users[1]), service.reserve(order.id, users[2]), return_exceptions=True)
    assert sum(isinstance(item, Match) for item in results) == 1
    assert sum(isinstance(item, DomainError) for item in results) == 1


@pytest.mark.skipif(not os.getenv('TEST_DATABASE_URL', '').startswith('postgresql'), reason='Requires PostgreSQL upsert')
async def test_duplicate_creation(db):
    sessions, users, _ = db
    service = OrderService(sessions)
    results = await asyncio.gather(*[service.create(users[0], 'BUY', '250', 'same-key') for _ in range(2)])
    assert results[0].id == results[1].id

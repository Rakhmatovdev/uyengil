import asyncio
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock
from app.services.exchange_rate_service import ExchangeRateService


async def test_cache_and_spam(db):
    sessions, _, _ = db
    service = ExchangeRateService(sessions)
    service.fetch_usd_rate = AsyncMock(return_value=(Decimal('12345.67'), date(2026, 9, 14)))
    await asyncio.gather(*[service.update_usd_rate() for _ in range(30)])
    assert service.fetch_usd_rate.await_count == 1
    cached = await service.get_current_usd_rate()
    assert cached.rate == Decimal('12345.67')


async def test_failure_preserves_rate_and_timestamp(db):
    sessions, _, _ = db
    service = ExchangeRateService(sessions, interval=0)
    service.fetch_usd_rate = AsyncMock(return_value=(Decimal('12345.67'), date(2026, 9, 14)))
    before = await service.update_usd_rate()
    service.fetch_usd_rate = AsyncMock(side_effect=RuntimeError('Offline'))
    after = await service.update_usd_rate()
    assert after.rate == before.rate
    assert after.updated_at == before.updated_at


async def test_empty_cache_does_not_fetch_on_read(db):
    sessions, _, _ = db
    service = ExchangeRateService(sessions)
    service.fetch_usd_rate = AsyncMock(side_effect=RuntimeError('Offline'))
    assert await service.get_current_usd_rate() is None
    service.fetch_usd_rate.assert_not_awaited()
    assert await service.update_usd_rate() is None

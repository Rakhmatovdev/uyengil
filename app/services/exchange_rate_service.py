import asyncio
import logging
import time
from datetime import datetime
from decimal import Decimal
import httpx
from sqlalchemy import select
from app.database.base import utcnow
from app.database.models import ExchangeRate

log = logging.getLogger(__name__)
CBU_URL = 'https://cbu.uz/oz/arkhiv-kursov-valyut/json/USD/'


class ExchangeRateService:
    def __init__(self, sessions, interval=1800):
        self.sessions = sessions
        self.interval = interval
        self.lock = asyncio.Lock()
        self.last_attempt = float('-inf')

    async def fetch_usd_rate(self):
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(CBU_URL)
            response.raise_for_status()
            rows = response.json()
        row = next(item for item in rows if item['Ccy'] == 'USD')
        rate = Decimal(row['Rate']) / Decimal(str(row['Nominal']))
        if not rate.is_finite() or rate <= 0:
            raise ValueError('Invalid CBU USD rate')
        return rate, datetime.strptime(row['Date'], '%d.%m.%Y').date()

    async def get_cached_usd_rate(self):
        async with self.sessions() as session:
            return await session.scalar(select(ExchangeRate).where(ExchangeRate.currency == 'USD'))

    async def get_current_usd_rate(self):
        return await self.get_cached_usd_rate()

    async def update_usd_rate(self):
        # One process in MVP; failed attempts are throttled as well as successes.
        async with self.lock:
            if time.monotonic() - self.last_attempt < self.interval:
                return await self.get_cached_usd_rate()
            self.last_attempt = time.monotonic()
            try:
                rate, rate_date = await self.fetch_usd_rate()
                async with self.sessions.begin() as session:
                    cached = await session.scalar(select(ExchangeRate).where(ExchangeRate.currency == 'USD'))
                    if cached is None:
                        cached = ExchangeRate(currency='USD', source='CBU')
                        session.add(cached)
                    elif rate_date < cached.rate_date:
                        raise ValueError('CBU returned an older rate date')
                    cached.rate, cached.rate_date, cached.updated_at = rate, rate_date, utcnow()
            except Exception:
                log.exception('CBU refresh failed; preserving last successful rate')
            return await self.get_cached_usd_rate()

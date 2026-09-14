import asyncio
import logging
import secrets
from contextlib import asynccontextmanager, suppress
from fastapi import FastAPI, Request, HTTPException
from pydantic import ValidationError
from aiogram.types import Update
from sqlalchemy import text
from app.config import Settings
from app.database.session import create_database
from app.services.exchange_rate_service import ExchangeRateService
from app.services.order_service import OrderService
from app.services.match_service import MatchService
from app.services.notification_service import deliver_notifications
from app.bot.bot import create_bot

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


async def rate_worker(rates):
    while True:
        try:
            await rates.update_usd_rate()
        except Exception:
            log.exception('Rate worker failed')
        await asyncio.sleep(rates.interval)


async def maintenance_worker(sessions, orders, bot, rates):
    while True:
        try:
            await orders.cleanup()
            await deliver_notifications(sessions, bot, rates)
        except Exception:
            log.exception('Maintenance worker failed')
        await asyncio.sleep(2)


@asynccontextmanager
async def lifespan(app):
    settings = Settings()
    engine, sessions = create_database(settings.database_url)
    rates = ExchangeRateService(sessions, settings.rate_refresh_seconds)
    orders = OrderService(sessions, settings.order_ttl_hours)
    matches = MatchService(sessions, settings.reservation_seconds)
    bot, dp = create_bot(settings, sessions=sessions, rates=rates, orders=orders, matches=matches)
    app.state.settings, app.state.engine = settings, engine
    app.state.bot, app.state.dp = bot, dp
    tasks = []
    try:
        async with engine.connect() as connection:
            await connection.execute(text('SELECT 1'))
        await bot.set_webhook(settings.webhook_base_url + '/telegram/webhook',
            secret_token=settings.webhook_secret, allowed_updates=dp.resolve_used_update_types())
        tasks = [asyncio.create_task(rate_worker(rates)),
                 asyncio.create_task(maintenance_worker(sessions, orders, bot, rates))]
        yield
    finally:
        for task in tasks:
            task.cancel()
        for task in tasks:
            with suppress(asyncio.CancelledError):
                await task
        await dp.storage.close()
        await dp.fsm.events_isolation.close()
        await bot.session.close()
        await engine.dispose()


app = FastAPI(title='Obmen Valyuta Bot', lifespan=lifespan)


@app.get('/health')
async def health():
    async with app.state.engine.connect() as connection:
        await connection.execute(text('SELECT 1'))
    return {'status': 'ok'}


@app.post('/telegram/webhook')
async def webhook(request: Request):
    provided = request.headers.get('X-Telegram-Bot-Api-Secret-Token', '')
    if not secrets.compare_digest(provided, app.state.settings.webhook_secret):
        raise HTTPException(403, 'Invalid webhook secret')
    try:
        update = Update.model_validate(await request.json(), context={'bot': app.state.bot})
    except (ValidationError, ValueError):
        raise HTTPException(400, 'Invalid Telegram update') from None
    # Await processing so failures return 5xx and Telegram can retry.
    await app.state.dp.feed_update(app.state.bot, update)
    return {'ok': True}

"""Local development entry point, using the same database and services."""
import asyncio
from contextlib import suppress
from app.config import Settings
from app.database.session import create_database
from app.bot.bot import create_bot
from app.services.exchange_rate_service import ExchangeRateService
from app.services.order_service import OrderService
from app.services.match_service import MatchService
from app.main import rate_worker, maintenance_worker


async def main():
    settings = Settings()
    engine, sessions = create_database(settings.database_url)
    rates = ExchangeRateService(sessions, settings.rate_refresh_seconds)
    orders = OrderService(sessions, settings.order_ttl_hours)
    matches = MatchService(sessions, settings.reservation_seconds)
    bot, dp = create_bot(settings, sessions=sessions, rates=rates, orders=orders, matches=matches)
    tasks = []
    try:
        await bot.delete_webhook(drop_pending_updates=False)
        tasks = [asyncio.create_task(rate_worker(rates)),
                 asyncio.create_task(maintenance_worker(sessions, orders, bot, rates))]
        await dp.start_polling(bot, close_bot_session=False)
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


if __name__ == '__main__':
    asyncio.run(main())

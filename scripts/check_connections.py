"""Read-only connectivity diagnostics; never prints credentials or request URLs."""
import asyncio
from aiogram import Bot
from dotenv import dotenv_values
from app.services.exchange_rate_service import ExchangeRateService


async def main():
    values = dotenv_values()
    bot = Bot(values['BOT_TOKEN'])
    try:
        me = await bot.get_me(request_timeout=15)
        print(f'Telegram: OK, @{me.username}')
    except Exception as exc:
        print(f'Telegram: {type(exc).__name__} (details omitted to protect credentials)')
    finally:
        await bot.session.close()
    try:
        rate, date = await ExchangeRateService(None).fetch_usd_rate()
        print(f'CBU: OK, rate date {date}, USD/UZS {rate}')
    except Exception as exc:
        print(f'CBU: {type(exc).__name__}')


if __name__ == '__main__':
    asyncio.run(main())

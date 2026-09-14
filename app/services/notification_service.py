import logging
from datetime import datetime, timedelta
from sqlalchemy import select
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest, TelegramRetryAfter
from app.database.base import utcnow
from app.database.models import Notification, Match
from app.bot.keyboards import confirmation
from app.bot.texts import rate_text, NOTICE

log = logging.getLogger(__name__)


async def deliver_notifications(sessions, bot, rates):
    # Durable outbox: retries after restart; Telegram delivery is at-least-once.
    for _ in range(50):
        async with sessions.begin() as session:
            item = await session.scalar(select(Notification).where(
                Notification.sent_at.is_(None), Notification.available_at <= utcnow()
            ).order_by(Notification.id).limit(1).with_for_update(skip_locked=True))
            if item is None:
                break
            payload, markup = item.payload, None
            if payload['kind'] == 'confirm':
                match = await session.get(Match, payload['match_id'])
                if match.status != 'PENDING' or datetime.fromisoformat(payload['expires_at']) <= utcnow():
                    item.sent_at = utcnow()
                    continue
                text = (f'Bitim #{match.id}\n\nSumma: {payload["amount"]} USD\n\n'
                    f'{await rate_text(rates)}\n\n{NOTICE}\n\n'
                    'Davom etasizmi? Reservation yaratilganidan 2 daqiqa ichida ikkala tomon tasdiqlashi kerak.')
                markup = confirmation(match.id)
            else:
                text = payload['text']
            try:
                await bot.send_message(item.telegram_id, text, reply_markup=markup)
                item.sent_at = utcnow()
            except TelegramRetryAfter as exc:
                item.available_at = utcnow() + timedelta(seconds=exc.retry_after + 1)
            except (TelegramForbiddenError, TelegramBadRequest):
                log.exception('Cannot deliver notification %s; retrying in one hour', item.id)
                item.available_at = utcnow() + timedelta(hours=1)
            except Exception:
                log.exception('Notification %s delivery failed', item.id)
                item.available_at = utcnow() + timedelta(seconds=30)

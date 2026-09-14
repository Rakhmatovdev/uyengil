from unittest.mock import AsyncMock
from sqlalchemy import select
from app.database.models import Notification
from app.services.match_service import MatchService
from app.services.exchange_rate_service import ExchangeRateService
from app.services.notification_service import deliver_notifications


async def test_delivery_failure_retains_outbox(db):
    sessions, users, order = db
    await MatchService(sessions).reserve(order.id, users[1])
    bot = AsyncMock()
    bot.send_message.side_effect = RuntimeError('network unavailable')
    await deliver_notifications(sessions, bot, ExchangeRateService(sessions))
    async with sessions() as session:
        items = list(await session.scalars(select(Notification)))
        assert len(items) == 2
        assert all(item.sent_at is None for item in items)


async def test_completed_match_suppresses_old_prompts_and_sends_contacts(db):
    sessions, users, order = db
    matches = MatchService(sessions)
    match = await matches.reserve(order.id, users[1])
    await matches.decide(match.id, users[0].id, True)
    await matches.decide(match.id, users[1].id, True)
    bot = AsyncMock()
    await deliver_notifications(sessions, bot, ExchangeRateService(sessions))
    assert bot.send_message.await_count == 2
    assert all('MATCH TOPILDI' in call.args[1] for call in bot.send_message.await_args_list)

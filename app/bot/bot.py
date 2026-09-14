import logging
from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import SimpleEventIsolation
from aiogram.types import CallbackQuery, Message
from app.services.user_service import register
from app.services.order_service import DomainError
from app.bot.handlers import start, buy, sell, orders, match, exchange_rate

log = logging.getLogger(__name__)


class UserMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        chat = event.chat if isinstance(event, Message) else getattr(event.message, 'chat', None)
        if chat is None or chat.type != 'private':
            if isinstance(event, CallbackQuery):
                await event.answer('Botdan shaxsiy chatda foydalaning.', show_alert=True)
            return
        sender = data.get('event_from_user')
        if sender:
            async with data['sessions'].begin() as session:
                data['user'] = await register(session, sender)
        try:
            return await handler(event, data)
        except DomainError as exc:
            if isinstance(event, CallbackQuery):
                await event.answer(str(exc), show_alert=True)
            elif isinstance(event, Message):
                await event.answer(str(exc))


def create_bot(settings, **services):
    bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode='HTML'))
    dp = Dispatcher(events_isolation=SimpleEventIsolation(), **services)
    middleware = UserMiddleware()
    dp.message.outer_middleware(middleware)
    dp.callback_query.outer_middleware(middleware)
    for module in (start, buy, sell, exchange_rate, orders, match):
        dp.include_router(module.router)
    return bot, dp

from aiogram import Router, F
from aiogram.types import CallbackQuery

router = Router()


@router.callback_query(F.data.startswith('reserve:'))
async def reserve(callback: CallbackQuery, matches, user):
    await matches.reserve(int(callback.data.split(':')[1]), user)
    await callback.answer('E’lon band qilindi. Tasdiqlash xabari yuborilmoqda.', show_alert=True)


@router.callback_query(F.data.startswith('match:'))
async def decide(callback: CallbackQuery, matches, user):
    _, action, match_id = callback.data.split(':')
    result = await matches.decide(int(match_id), user.id, action == 'yes')
    await callback.answer(result, show_alert=True)

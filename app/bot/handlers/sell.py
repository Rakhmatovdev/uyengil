from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from .buy import begin

router = Router()


@router.message(F.text == 'Dollar sotaman')
async def sell(message: Message, state: FSMContext, rates, user):
    await begin(message, state, rates, user, 'SELL')

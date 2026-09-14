from aiogram import Router, F
from aiogram.types import Message
from app.bot.texts import rate_text

router = Router()


@router.message(F.text == 'Kursni yangilash')
async def refresh(message: Message, rates):
    # This button reads the latest database snapshot; only the worker calls CBU.
    await message.answer(f'Joriy USD kursi\n\n{await rate_text(rates)}')

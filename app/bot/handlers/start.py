from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from app.bot.keyboards import MENU
from app.bot.texts import NOTICE, rate_text

router = Router()


@router.message(CommandStart())
@router.message(Command('cancel'))
async def start(message: Message, state: FSMContext, rates):
    await state.clear()
    await message.answer(f'OBMEN\n\n{await rate_text(rates)}\n\n{NOTICE}\n\nNima qilmoqchisiz?', reply_markup=MENU)

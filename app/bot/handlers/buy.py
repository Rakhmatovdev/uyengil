from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from app.bot.states import CreateOrder
from app.bot.texts import rate_text

router = Router()


async def begin(message: Message, state: FSMContext, rates, user, kind):
    await state.clear()
    if not user.username:
        await message.answer('Kontakt almashish uchun Telegram sozlamalarida username o‘rnating, so‘ng /start bosing.')
        return
    await state.set_state(CreateOrder.amount)
    await state.update_data(kind=kind)
    verb = 'olmoqchisiz' if kind == 'BUY' else 'sotmoqchisiz'
    await message.answer(f'{await rate_text(rates)}\n\nQancha USD {verb}?\nMasalan: 500\n\nBekor qilish: /cancel')


@router.message(F.text == 'Dollar olaman')
async def buy(message: Message, state: FSMContext, rates, user):
    await begin(message, state, rates, user, 'BUY')

from uuid import uuid4
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from app.bot.states import CreateOrder
from app.bot.keyboards import inline, MENU
from app.bot.texts import rate_text, NOTICE
from app.services.order_service import parse_amount

router = Router()


@router.message(F.text.in_({"Aktiv e'lonlar", "Mening e'lonlarim"}))
async def orders_menu(message: Message, state: FSMContext, orders, user, rates):
    await state.clear()
    await show_orders(message, orders, user, rates, message.text == "Mening e'lonlarim", 0)


async def show_orders(message, orders, user, rates, mine, offset):
    items = await orders.list(user.id, mine, offset)
    title = 'MENING E’LONLARIM' if mine else 'AKTIV E’LONLAR'
    await message.answer(f'{title}\n\n{await rate_text(rates)}')
    if not items:
        await message.answer('Hozircha e’lonlar yo‘q.', reply_markup=MENU)
    for order in items[:5]:
        label = 'Sotiladi' if order.type == 'SELL' else 'Sotib olinadi'
        buttons = None
        if order.status == 'ACTIVE':
            buttons = inline([[('❌ Bekor qilish', f'cancel:{order.id}')]]) if mine else inline([
                [('Olaman' if order.type == 'SELL' else 'Sotaman', f'reserve:{order.id}')]])
        await message.answer(f'#{order.id} — {order.amount} USD\n{label}\nHolat: {order.status}', reply_markup=buttons)
    nav = []
    if offset:
        nav.append(('← Oldingi', f'page:{int(mine)}:{max(0, offset-5)}'))
    if len(items) > 5:
        nav.append(('Keyingi →', f'page:{int(mine)}:{offset+5}'))
    if nav:
        await message.answer('Sahifalar', reply_markup=inline([nav]))


@router.callback_query(F.data.startswith('page:'))
async def page(callback: CallbackQuery, orders, user, rates):
    _, mine, offset = callback.data.split(':')
    await callback.answer()
    await show_orders(callback.message, orders, user, rates, bool(int(mine)), max(0, int(offset)))


@router.callback_query(F.data.startswith('cancel:'))
async def cancel(callback: CallbackQuery, orders, user):
    await orders.cancel(int(callback.data.split(':')[1]), user.id)
    await callback.answer('E’lon bekor qilindi.')
    await callback.message.edit_reply_markup(reply_markup=None)


@router.message(CreateOrder.amount, F.text)
async def amount(message: Message, state: FSMContext, rates):
    amount = parse_amount(message.text)
    key = str(uuid4())
    await state.update_data(amount=str(amount), key=key)
    await state.set_state(CreateOrder.preview)
    data = await state.get_data()
    label = 'Dollar olish' if data['kind'] == 'BUY' else 'Dollar sotish'
    await message.answer(f'{label}\n\nSumma: {amount} USD\n\n{await rate_text(rates)}\n\n{NOTICE}\n\nE’lonni joylaysizmi?',
        reply_markup=inline([[('✅ Joylash', f'draft:post:{key}')],
            [('✏️ O‘zgartirish', f'draft:edit:{key}'), ('❌ Bekor qilish', f'draft:cancel:{key}')]]))


@router.callback_query(F.data.startswith('draft:'))
async def draft(callback: CallbackQuery, state: FSMContext, orders, user):
    _, action, key = callback.data.split(':')
    data = await state.get_data()
    if await state.get_state() != CreateOrder.preview.state or data.get('key') != key:
        await callback.answer('Bu tugma eskirgan. Menyudan qayta boshlang.', show_alert=True)
        return
    if action == 'post':
        order = await orders.create(user, data['kind'], data['amount'], key)
        await state.clear()
        await callback.message.answer(f'E’lon #{order.id} joylandi. Holat: ACTIVE', reply_markup=MENU)
    elif action == 'edit':
        await state.set_state(CreateOrder.amount)
        await callback.message.answer('Yangi USD summasini kiriting:')
    else:
        await state.clear()
        await callback.message.answer('Bekor qilindi.', reply_markup=MENU)
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

MENU = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Dollar olaman'), KeyboardButton(text='Dollar sotaman')],
    [KeyboardButton(text="Aktiv e'lonlar"), KeyboardButton(text="Mening e'lonlarim")],
    [KeyboardButton(text='Kursni yangilash')]], resize_keyboard=True)


def inline(rows):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text, callback_data=data) for text, data in row] for row in rows])


def confirmation(match_id):
    return inline([[('✅ Tasdiqlayman', f'match:yes:{match_id}'),
                    ('❌ Bekor qilish', f'match:no:{match_id}')]])

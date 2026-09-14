from datetime import timedelta, timezone

NOTICE = ('Markaziy bank rasmiy kursi — faqat ma’lumot uchun. '
          'Bitim shartlarini tomonlar Telegram orqali kelishadi. '
          'Bot pul qabul qilmaydi va tranzaksiya amalga oshirmaydi.')


async def rate_text(rates):
    rate = await rates.get_current_usd_rate()
    if rate is None:
        return 'Rasmiy kurs vaqtincha mavjud emas. Botdan foydalanishingiz mumkin.'
    stamp = rate.updated_at
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    stamp = stamp.astimezone(timezone(timedelta(hours=5)))
    amount = f'{rate.rate:,.2f}'.replace(',', ' ')
    return (f'1 USD = {amount} UZS\nMarkaziy bank rasmiy kursi\n'
            f'Kurs sanasi: {rate.rate_date:%d.%m.%Y}\n'
            f'Oxirgi yangilanish: {stamp:%d.%m.%Y %H:%M} (Toshkent)')

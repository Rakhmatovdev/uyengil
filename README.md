# Obmen Valyuta Bot

Telegram’da USD olish va sotish e’lonlari uchun P2P matching MVP.
Bot mablag‘larni qabul qilmaydi, saqlamaydi yoki o‘tkazmaydi. CBU kursi faqat ma’lumot uchun.

## Ishga tushirish

1. `.env.example` faylini `.env` ga nusxalang. BotFather tokenini, ochiq HTTPS domenni va tasodifiy webhook secretni kiriting.
2. Docker Desktop / Docker Engine’ni ishga tushiring.
3. Compose uchun `DATABASE_URL=postgresql+asyncpg://obmen:obmen@db:5432/obmen` bo‘lsin.
4. `docker compose up --build -d` buyrug‘ini bajaring. Migratsiya avtomatik bajariladi.
5. HTTPS reverse proxy orqali domenni `127.0.0.1:8000` ga yo‘naltiring. Webhook: `/telegram/webhook`.
6. Botda `/start` bosing. `/health` DB ulanishini tekshiradi.

## Bepul Render deploy

Render free web service uchun `render.yaml` tayyor. Repository’ni GitHub’ga push qilib, Render’da **New → Blueprint** orqali shu repository’ni tanlang. Render service yaratilgach, `BOT_TOKEN`, `DATABASE_URL` va `WEBHOOK_SECRET` secret qiymatlarini kiriting. `DATABASE_URL` bepul Neon yoki Supabase PostgreSQL’ning **asyncpg** URL’i bo‘lishi kerak: `postgresql+asyncpg://...`. `WEBHOOK_BASE_URL` Render bergan haqiqiy HTTPS URL bilan mos bo‘lsin. Deploy tugagach `/health` ni ochib, Telegram’da `/start` yuboring.

Render free service ishlatilmaganda uxlaydi; birinchi so‘rovda uyg‘onishi bir necha soniya olishi mumkin. Uyg‘oq saqlash uchun tashqi cron ping ishlatilishi mumkin, ammo bu Render free limitlariga bog‘liq. Neon/Supabase bazasi uchun alohida free loyiha yarating; lokal Docker PostgreSQL URL’ini Render’ga bermang.

GitHub’ga `.env`, `.venv`, `.uv-cache` yoki `migration-test.db` yubormang. Token oldin chatda ko‘ringani uchun production deploydan oldin BotFather’da tokenni rotate qilish tavsiya etiladi.

PostgreSQL parolini o‘zgartirsangiz, `POSTGRES_PASSWORD` va `DATABASE_URL` qiymatlarini moslang.
`.env` maxfiy fayl: Git va Docker build context’dan chiqarilgan.

## Lokal ishlash

Python 3.12+ va PostgreSQL kerak:

```powershell
uv venv --python 3.12
uv pip install -r requirements-dev.txt
.venv\Scripts\alembic upgrade head
.venv\Scripts\uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
```

Lokal DB uchun `.env` dagi host `localhost`, Compose ichida `db`.

HTTPS domen hali bo‘lmasa, migratsiyadan keyin `.venv\Scripts\python -m app.polling` ishlating.
Bu rejim mavjud webhook’ni o‘chirib polling’ni yoqadi; webhook serveri bilan bir vaqtda ishlatmang.

## Xatti-harakat

- `/start` foydalanuvchini ro‘yxatga oladi va mavjud profilini yangilaydi.
- Kontakt almashish uchun Telegram username kerak; telefon raqami yig‘ilmaydi.
- BUY va SELL e’lonlari, summa kiritish, tahrirlash, joylash va bekor qilish mavjud.
- Aktiv e’lonlarda o‘z e’loningiz ko‘rsatilmaydi; ro‘yxatlar 5 tadan sahifalanadi.
- Summa `Decimal`, 0.01–100 000 000 USD, ko‘pi bilan ikki kasr raqami.
- `SELECT FOR UPDATE` bir e’lonni parallel band qilishni seriallashtiradi.
- Har reservation alohida match ID oladi; eski tugmalar keyingi reservationni tasdiqlay olmaydi.
- Ikkala tomon alohida tasdiqlaydi. Faqat shundan so‘ng kontakt xabarlari yaratiladi.
- Reservation 120 soniya. Worker har 2 soniyada muddatlarni tekshiradi; amal bajarishda ham muddat tekshiriladi.
- E’lon muddati standart 24 soat (`ORDER_TTL_HOURS`). Reservation davomida e’lon muddati tugasa, mavjud reservation o‘z 120 soniyasini tugatishi mumkin.
- CBU har 30 daqiqada worker orqali yangilanadi. `/start` va «Kursni yangilash» faqat DB cache’ni o‘qiydi.
- CBU xatosida eski kurs va uning yangilanish vaqti saqlanadi; bo‘sh cache botni to‘xtatmaydi.
- Kursning amal qilish sanasi va oxirgi muvaffaqiyatli tekshirish vaqti alohida, Toshkent vaqtida ko‘rsatiladi.
- Kontakt va tasdiq xabarlari tranzaksiyada outbox’ga yoziladi, worker xatolarda qayta yuboradi. Telegram bilan exactly-once kafolati yo‘q: jo‘natilgandan keyin jarayon uzilsa, xabar takrorlanishi mumkin.
- Webhook secret tekshiriladi; muvaffaqiyatsiz handler HTTP 5xx qaytaradi.

## MVP chegaralari

Faqat **bitta bot process / bitta Uvicorn worker** ishlating. Draftlar va FSM xotirada, restartda tugallanmagan draft yo‘qoladi; e’lonlar, reservation, tasdiqlar, kurs va outbox PostgreSQL’da saqlanadi. Ko‘p replika uchun Redis FSM va taqsimlangan scheduler kerak.
Telegram username foydalanuvchining oxirgi bot murojaatidan yangilanadi; keyinchalik o‘zgartirilgan username eskirishi mumkin.
Serverga deploy qilish, DNS va TLS sozlash alohida infratuzilma talab qiladi.

## Testlar

```powershell
.venv\Scripts\pytest -q
.venv\Scripts\ruff check .
```

Standart testlar vaqtinchalik SQLite’da biznes qoidalarini tekshiradi. PostgreSQL’ga xos parallel reservation va upsert testlari uchun **alohida bo‘sh test DB** ishlating:

```powershell
$env:TEST_DATABASE_URL = 'postgresql+asyncpg://obmen:obmen@localhost:5432/obmen_test'
.venv\Scripts\pytest -q
```

Test fixture shu test bazasidagi MVP jadvallarini yaratadi va testdan keyin o‘chiradi. Ishchi DB URL’ini bermang.

Rasmiy manbalar: [CBU dasturchilar uchun](https://cbu.uz/oz/arkhiv-kursov-valyut/veb-masteram/), [Aiogram webhook](https://docs.aiogram.dev/en/latest/api/methods/set_webhook.html), [SQLAlchemy async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html).

# uyengil

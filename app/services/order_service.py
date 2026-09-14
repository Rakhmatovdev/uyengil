import re
from datetime import timedelta, timezone
from decimal import Decimal
from sqlalchemy import select
from app.database.base import utcnow
from app.database.models import Order, Match


class DomainError(ValueError):
    pass


def parse_amount(raw):
    value = raw.strip().replace(',', '.')
    if not re.fullmatch(r'\d{1,9}(?:\.\d{1,2})?', value):
        raise DomainError('Musbat summa kiriting. Masalan: 500 yoki 500.50')
    amount = Decimal(value)
    if not Decimal('0.01') <= amount <= Decimal('100000000'):
        raise DomainError('Summa 0.01 dan 100 000 000 USD gacha bo‘lishi kerak.')
    return amount


def aware(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


async def expire_order(session, order, now):
    if order.status == 'RESERVED':
        match = await session.scalar(select(Match).where(Match.order_id == order.id, Match.status == 'PENDING'))
        if match and aware(match.expires_at) <= now:
            match.status = 'EXPIRED'
            order.status, order.reserved_by, order.reserved_at = 'ACTIVE', None, None
    if order.status == 'ACTIVE' and aware(order.expires_at) <= now:
        order.status = 'EXPIRED'


class OrderService:
    def __init__(self, sessions, ttl_hours=24):
        self.sessions, self.ttl_hours = sessions, ttl_hours

    async def create(self, user, kind, amount, creation_key):
        if not user.username:
            raise DomainError('Avval Telegram sozlamalarida username o‘rnating va /start bosing.')
        if kind not in ('BUY', 'SELL'):
            raise DomainError('Noto‘g‘ri e’lon turi.')
        amount = parse_amount(str(amount))
        async with self.sessions.begin() as session:
            # PostgreSQL upsert makes repeated Telegram delivery idempotent.
            from sqlalchemy.dialects.postgresql import insert
            stmt = insert(Order).values(user_id=user.id, type=kind, amount=amount,
                creation_key=creation_key, expires_at=utcnow() + timedelta(hours=self.ttl_hours))
            await session.execute(stmt.on_conflict_do_nothing(index_elements=[Order.creation_key]))
            return await session.scalar(select(Order).where(Order.creation_key == creation_key, Order.user_id == user.id))

    async def list(self, user_id, mine=False, offset=0):
        await self.cleanup()
        async with self.sessions() as session:
            query = select(Order)
            if mine:
                query = query.where(Order.user_id == user_id)
            else:
                query = query.where(Order.user_id != user_id, Order.status == 'ACTIVE')
            return list((await session.scalars(query.order_by(Order.id.desc()).offset(offset).limit(6))).all())

    async def cancel(self, order_id, user_id):
        async with self.sessions.begin() as session:
            order = await session.scalar(select(Order).where(Order.id == order_id).with_for_update())
            if not order or order.user_id != user_id:
                raise DomainError('E’lon topilmadi.')
            await expire_order(session, order, utcnow())
            if order.status != 'ACTIVE':
                raise DomainError('Faqat aktiv e’lonni bekor qilish mumkin.')
            order.status = 'CANCELLED'

    async def cleanup(self):
        async with self.sessions.begin() as session:
            orders = await session.scalars(select(Order).where(
                Order.status.in_(['ACTIVE', 'RESERVED']),
                (Order.expires_at <= utcnow()) | (Order.status == 'RESERVED')
            ).with_for_update(skip_locked=True))
            for order in orders:
                await expire_order(session, order, utcnow())

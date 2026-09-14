from datetime import timedelta
from html import escape
from sqlalchemy import select
from app.database.base import utcnow
from app.database.models import Order, Match, User, Notification
from app.services.order_service import DomainError, expire_order


class MatchService:
    def __init__(self, sessions, reservation_seconds=120):
        self.sessions, self.reservation_seconds = sessions, reservation_seconds

    async def reserve(self, order_id, user):
        if not user.username:
            raise DomainError('Telegram username o‘rnating va /start bosing.')
        async with self.sessions.begin() as session:
            order = await session.scalar(select(Order).where(Order.id == order_id).with_for_update())
            if not order or order.user_id == user.id:
                raise DomainError('Bu e’lonni tanlay olmaysiz.')
            await expire_order(session, order, utcnow())
            if order.status != 'ACTIVE':
                raise DomainError('Bu e’lon band yoki faol emas. Boshqa e’lonni tanlang.')
            owner = await session.get(User, order.user_id)
            if not owner.username:
                raise DomainError('E’lon egasining Telegram username’i mavjud emas.')
            order.status, order.reserved_by, order.reserved_at = 'RESERVED', user.id, utcnow()
            match = Match(order_id=order.id,
                seller_id=owner.id if order.type == 'SELL' else user.id,
                buyer_id=user.id if order.type == 'SELL' else owner.id,
                expires_at=utcnow() + timedelta(seconds=self.reservation_seconds))
            session.add(match)
            await session.flush()
            for participant in (owner, user):
                session.add(Notification(telegram_id=participant.telegram_id, payload={
                    'kind': 'confirm', 'match_id': match.id, 'amount': str(order.amount),
                    'expires_at': match.expires_at.isoformat()}))
            return match

    async def decide(self, match_id, user_id, confirm):
        result = 'Tasdiq qabul qilindi. Qarshi tomon tasdig‘i kutilmoqda.'
        async with self.sessions.begin() as session:
            order_id = await session.scalar(select(Match.order_id).where(Match.id == match_id))
            if order_id is None:
                raise DomainError('Bitim topilmadi.')
            order = await session.scalar(select(Order).where(Order.id == order_id).with_for_update())
            match = await session.get(Match, match_id)
            if user_id not in (match.seller_id, match.buyer_id):
                raise DomainError('Bu bitim sizga tegishli emas.')
            await expire_order(session, order, utcnow())
            if match.status == 'MATCHED':
                result = 'Bitim allaqachon tasdiqlangan. Kontaktlar yuborilgan.'
            elif match.status != 'PENDING' or order.status != 'RESERVED':
                result = 'Bu reservation tugagan. Aktiv e’lonlardan qayta tanlang.'
            elif not confirm:
                match.status = 'CANCELLED'
                order.status, order.reserved_by, order.reserved_at = 'ACTIVE', None, None
                await expire_order(session, order, utcnow())
                result = 'Reservation bekor qilindi.'
                for participant_id in (match.seller_id, match.buyer_id):
                    participant = await session.get(User, participant_id)
                    session.add(Notification(telegram_id=participant.telegram_id,
                        payload={'kind': 'text', 'text': result}))
            else:
                if user_id == match.seller_id:
                    match.seller_confirmed = True
                else:
                    match.buyer_confirmed = True
                if match.seller_confirmed and match.buyer_confirmed:
                    seller = await session.get(User, match.seller_id)
                    buyer = await session.get(User, match.buyer_id)
                    if not seller.username or not buyer.username:
                        raise DomainError('Tomonlardan birida username yo‘q. Reservationni bekor qiling.')
                    order.status = match.status = 'MATCHED'
                    match.matched_at = utcnow()
                    for recipient, contact, label in ((seller, buyer, 'Xaridor'), (buyer, seller, 'Sotuvchi')):
                        session.add(Notification(telegram_id=recipient.telegram_id, payload={
                            'kind': 'text', 'text': f'MATCH TOPILDI\n\nSumma: {order.amount} USD\n\n'
                            f'{label}: {escape(contact.first_name)}\n@{escape(contact.username)}\n\n'
                            'Telegram orqali bog‘laning. Ayirboshlash shartlarini o‘zaro kelishing.'}))
                    result = 'MATCH TOPILDI! Kontaktlar yuborilmoqda.'
        return result

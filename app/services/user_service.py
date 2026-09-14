from sqlalchemy.dialects.postgresql import insert
from app.database.models import User
from app.database.base import utcnow


async def register(session, telegram_user):
    stmt = insert(User).values(telegram_id=telegram_user.id,
        username=telegram_user.username, first_name=telegram_user.first_name)
    stmt = stmt.on_conflict_do_update(index_elements=[User.telegram_id], set_={
        'username': telegram_user.username, 'first_name': telegram_user.first_name,
        'updated_at': utcnow()}).returning(User)
    return (await session.execute(stmt)).scalar_one()

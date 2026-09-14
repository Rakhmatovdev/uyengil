from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, Boolean, Index, text
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base, utcnow


class Match(Base):
    __tablename__ = 'matches'
    __table_args__ = (Index('uq_live_order_match', 'order_id', unique=True,
        postgresql_where=text("status IN ('PENDING', 'MATCHED')"),
        sqlite_where=text("status IN ('PENDING', 'MATCHED')")),)
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey('orders.id'), index=True)
    seller_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    buyer_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    status: Mapped[str] = mapped_column(String(12), default='PENDING')
    seller_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    buyer_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    matched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

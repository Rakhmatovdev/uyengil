from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Numeric, ForeignKey, DateTime, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base, utcnow


class Order(Base):
    __tablename__ = 'orders'
    __table_args__ = (
        CheckConstraint('amount > 0'),
        CheckConstraint("type IN ('BUY', 'SELL')"),
        CheckConstraint("status IN ('ACTIVE', 'RESERVED', 'MATCHED', 'CANCELLED', 'EXPIRED')"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    type: Mapped[str] = mapped_column(String(4))
    currency: Mapped[str] = mapped_column(String(3), default='USD')
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    status: Mapped[str] = mapped_column(String(12), default='ACTIVE', index=True)
    reserved_by: Mapped[int | None] = mapped_column(ForeignKey('users.id'))
    reserved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    creation_key: Mapped[str] = mapped_column(String(36), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

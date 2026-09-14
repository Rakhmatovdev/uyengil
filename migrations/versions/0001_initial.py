"""Initial MVP schema."""
from alembic import op
import sqlalchemy as sa

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('users', sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False, unique=True),
        sa.Column('username', sa.String(64)), sa.Column('first_name', sa.String(256), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False))
    op.create_table('orders', sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('type', sa.String(4), nullable=False), sa.Column('currency', sa.String(3), nullable=False),
        sa.Column('amount', sa.Numeric(14, 2), nullable=False), sa.Column('status', sa.String(12), nullable=False),
        sa.Column('reserved_by', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('reserved_at', sa.DateTime(timezone=True)),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('creation_key', sa.String(36), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint('amount > 0'), sa.CheckConstraint("type IN ('BUY', 'SELL')"),
        sa.CheckConstraint("status IN ('ACTIVE', 'RESERVED', 'MATCHED', 'CANCELLED', 'EXPIRED')"))
    for column in ('user_id', 'status', 'expires_at'):
        op.create_index(f'ix_orders_{column}', 'orders', [column])
    op.create_table('matches', sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('order_id', sa.Integer(), sa.ForeignKey('orders.id'), nullable=False),
        sa.Column('seller_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('buyer_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('status', sa.String(12), nullable=False),
        sa.Column('seller_confirmed', sa.Boolean(), nullable=False), sa.Column('buyer_confirmed', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False), sa.Column('matched_at', sa.DateTime(timezone=True)))
    op.create_index('ix_matches_order_id', 'matches', ['order_id'])
    op.create_index('uq_live_order_match', 'matches', ['order_id'], unique=True,
        postgresql_where=sa.text("status IN ('PENDING', 'MATCHED')"), sqlite_where=sa.text("status IN ('PENDING', 'MATCHED')"))
    op.create_table('exchange_rates', sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('currency', sa.String(3), nullable=False, unique=True), sa.Column('rate', sa.Numeric(18, 6), nullable=False),
        sa.Column('source', sa.String(8), nullable=False), sa.Column('rate_date', sa.Date(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False))
    op.create_table('notifications', sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False), sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('available_at', sa.DateTime(timezone=True), nullable=False), sa.Column('sent_at', sa.DateTime(timezone=True)))


def downgrade():
    for table in ('notifications', 'exchange_rates', 'matches', 'orders', 'users'):
        op.drop_table(table)

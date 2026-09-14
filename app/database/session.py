from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.engine import make_url


def normalize_database_url(url: str) -> str:
    """Accept Neon/Supabase's standard URL while using SQLAlchemy asyncpg."""
    parsed = make_url(url)
    if parsed.drivername in ('postgresql', 'postgres'):
        parsed = parsed.set(drivername='postgresql+asyncpg')
    query = dict(parsed.query)
    # asyncpg uses `ssl`; libpq-only options otherwise cause connection errors.
    if 'sslmode' in query and 'ssl' not in query:
        query['ssl'] = query.pop('sslmode')
    query.pop('channel_binding', None)
    return str(parsed.set(query=query))


def create_database(url):
    engine = create_async_engine(normalize_database_url(url), pool_pre_ping=True)
    return engine, async_sessionmaker(engine, expire_on_commit=False)

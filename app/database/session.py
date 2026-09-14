from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.engine import make_url


def normalize_database_url(url: str) -> str:
    """Accept Neon/Supabase's standard URL while using SQLAlchemy asyncpg."""
    parsed = make_url(url)
    if parsed.drivername in ('postgresql', 'postgres'):
        parsed = parsed.set(drivername='postgresql+asyncpg')
    query = dict(parsed.query)
    # asyncpg uses `ssl`; libpq-only options otherwise cause connection errors.
    sslmode = query.pop('sslmode', None)
    if sslmode is not None and 'ssl' not in query:
        query['ssl'] = sslmode
    query.pop('channel_binding', None)
    # str(URL) redacts the password to '***', which breaks authentication.
    # This string is for the database driver only and must never be logged.
    return parsed.set(query=query).render_as_string(hide_password=False)


def create_database(url):
    engine = create_async_engine(normalize_database_url(url), pool_pre_ping=True)
    return engine, async_sessionmaker(engine, expire_on_commit=False)

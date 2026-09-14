from app.database.session import normalize_database_url
from sqlalchemy.engine import make_url, URL
from app.database.session import create_database


def test_neon_url_is_normalized_for_asyncpg():
    url = normalize_database_url(
        'postgresql://user:pass@example.neon.tech/db?sslmode=require&channel_binding=require')
    assert url == 'postgresql+asyncpg://user:pass@example.neon.tech/db?ssl=require'


async def test_driver_receives_original_password():
    original_password = 'test@:/?#%+ password'
    original = URL.create('postgresql', username='user', password=original_password,
        host='example.neon.tech', database='db', query={'sslmode': 'require'})
    engine, _ = create_database(original.render_as_string(hide_password=False))
    try:
        _, kwargs = engine.sync_engine.dialect.create_connect_args(engine.url)
        assert kwargs['password'] == original_password
        assert kwargs['ssl'] == 'require'
    finally:
        await engine.dispose()


def test_asyncpg_url_preserves_ssl_and_removes_libpq_options():
    normalized = make_url(normalize_database_url(
        'postgresql+asyncpg://user:pass@host/db?ssl=verify-full&sslmode=require&channel_binding=require'))
    assert normalized.password == 'pass'
    assert dict(normalized.query) == {'ssl': 'verify-full'}

from app.database.session import normalize_database_url


def test_neon_url_is_normalized_for_asyncpg():
    url = normalize_database_url(
        'postgresql://user:pass@example.neon.tech/db?sslmode=require&channel_binding=require')
    assert url == 'postgresql+asyncpg://user:***@example.neon.tech/db?ssl=require'

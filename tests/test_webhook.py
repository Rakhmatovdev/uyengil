from types import SimpleNamespace
from unittest.mock import AsyncMock
import httpx
from app.main import app


async def test_webhook_rejects_missing_secret_before_parsing():
    app.state.settings = SimpleNamespace(webhook_secret='a' * 32)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
        response = await client.post('/telegram/webhook', content='invalid')
    assert response.status_code == 403


async def test_webhook_validates_update_and_awaits_processing():
    app.state.settings = SimpleNamespace(webhook_secret='a' * 32)
    app.state.bot = None
    app.state.dp = SimpleNamespace(feed_update=AsyncMock())
    headers = {'X-Telegram-Bot-Api-Secret-Token': 'a' * 32}
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
        invalid = await client.post('/telegram/webhook', json={'bad': 1}, headers=headers)
        assert invalid.status_code == 400
        valid = await client.post('/telegram/webhook', json={'update_id': 42}, headers=headers)
        assert valid.status_code == 200
    app.state.dp.feed_update.assert_awaited_once()

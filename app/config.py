from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    bot_token: str
    database_url: str
    webhook_base_url: str
    webhook_secret: str = Field(min_length=32, max_length=256, pattern=r'^[A-Za-z0-9_-]+$')
    rate_refresh_seconds: int = Field(default=1800, ge=60)
    reservation_seconds: int = Field(default=120, ge=1)
    order_ttl_hours: int = Field(default=24, ge=1)

    @field_validator('webhook_base_url')
    @classmethod
    def https_only(cls, value):
        if not value.startswith('https://'):
            raise ValueError('Webhook URL must use HTTPS')
        return value.rstrip('/')

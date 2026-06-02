from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "delivery-route-optimizer"
    app_env: str = "dev"
    log_level: str = "debug"
    
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    database_url: str = "postgresql+asyncpg://app:app@localhost:5433/delivery_routes"
    redis_url: str = "redis://localhost:6379/0"
    readiness_timeout_seconds: float = 2.0
    
    database_echo: bool = False
    database_pool_size: int = 5
    database_max_overflow: int = 10
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "delivery-route-optimizer"
    app_env: str = "development"
    log_level: str = "debug"
    
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    database_url: str = ""
    redis_url: str = ""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()
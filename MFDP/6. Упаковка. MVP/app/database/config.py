from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional, Any


class Settings(BaseSettings):
    POSTGRES_HOST: Optional[str] = None
    POSTGRES_PORT: Optional[int] = None
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None

    # Application settings
    APP_NAME: Optional[str] = None
    APP_DESCRIPTION: Optional[str] = None
    DEBUG: Optional[bool] = None
    API_VERSION: Optional[str] = None
    
    @property
    def DATABASE_URL_asyncpg(self):
        return f'postgresql+asyncpg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}'
    
    @property
    def DATABASE_URL_psycopg(self):
        return f'postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}'
    
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    def validate(self) -> None:
        if not all([self.POSTGRES_HOST, self.POSTGRES_DB, self.POSTGRES_USER, self.POSTGRES_PASSWORD]):
            raise ValueError("Missing required database configuration.")

@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    settings.validate()
    return settings

from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    APP_NAME: str = "Smart Pocket Doctor"
    ALLOWED_ORIGINS: List[str] = ["*"] # tighten in production
    DATABASE_URL: str = "sqlite:///./test.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "my-secret-key"

    class Config:
        env_file = ".env"

settings = Settings()
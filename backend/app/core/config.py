from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
from urllib.parse import quote

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    PROJECT_NAME: str = "DMARC Analytics Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    # Anything other than "production" exposes sanitized error details
    ENVIRONMENT: str = "production"

    # Required: generate with `openssl rand -hex 32`
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"

    ELASTICSEARCH_URL: str = "http://localhost:9200"
    ELASTICSEARCH_USERNAME: str = "elastic"
    ELASTICSEARCH_PASSWORD: str
    ELASTICSEARCH_INDEX_PREFIX: str = "dmarc"

    # Redis settings for rate limiting and session management
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]

    # Bootstrap system admin, created on startup only if no users exist
    ADMIN_EMAIL: Optional[str] = None
    ADMIN_PASSWORD: Optional[str] = None

    # Email notification settings
    SMTP_SERVER: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    FROM_EMAIL: str = "alerts@dmarcanalytics.com"

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_strong(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return v

    @property
    def REDIS_URL(self) -> str:
        auth = f":{quote(self.REDIS_PASSWORD, safe='')}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

settings = Settings()

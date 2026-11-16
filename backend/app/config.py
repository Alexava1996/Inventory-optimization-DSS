from functools import lru_cache
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "sqlite:///./inventory.db"
    app_env: str = "development"
    app_origin: str = "http://localhost:3000"
    allowed_hosts: str = "localhost,127.0.0.1,testserver,api"
    session_hours: int = 8

    @model_validator(mode="after")
    def production(self):
        if self.app_env not in {"development", "test", "production"}:
            raise ValueError("APP_ENV non valido")
        if self.session_hours < 1 or self.session_hours > 24:
            raise ValueError("SESSION_HOURS deve essere compreso tra 1 e 24")
        if self.app_env == "production":
            if not self.app_origin.startswith("https://"):
                raise ValueError("In produzione APP_ORIGIN deve usare HTTPS")
            if not self.database_url.startswith("postgresql+psycopg://"):
                raise ValueError("In produzione è richiesto PostgreSQL con psycopg")
            if "*" in self.allowed_hosts:
                raise ValueError("ALLOWED_HOSTS non può contenere wildcard")
        return self


@lru_cache
def settings():
    return Settings()

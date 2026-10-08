"""Application settings, overridable through environment variables or a .env file."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Address Book API"
    database_url: str = "sqlite:///./address_book.db"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="ADDRESS_BOOK_")


settings = Settings()

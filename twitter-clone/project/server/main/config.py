import logging
import os
import pathlib
from functools import lru_cache

from httpx import URL

# from pydantic_core import Url
from pydantic_settings import BaseSettings, SettingsConfigDict

log = logging.getLogger("uvicorn")


class Settings(BaseSettings):
    environment: str = os.getenv("ENVIRONMENT", "dev")
    testing: str | bool = os.getenv("TESTING", False)
    database_url: str | None = os.getenv("DATABASE_URL")
    base_url: URL | str = os.getenv("BASE_URL", "")  # TODO URL type to check
    base_dir: pathlib.Path = pathlib.Path(__file__).parent.parent

    if environment == "dev":
        model_config = SettingsConfigDict(env_file=".env.dev")
    elif environment == "test":
        model_config = SettingsConfigDict(env_file=".env.test")


@lru_cache
def get_settings() -> Settings:
    log.info("Loading configuration...")
    return Settings()

import logging
import os
import pathlib
from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger("uvicorn")

env_file_map = {"dev": ".env.dev", "test": ".env.test"}


class Settings(BaseSettings):
    environment: str | None = os.getenv("ENVIRONMENT", "dev")
    testing: str | None = os.getenv("TESTING")

    load_dotenv(env_file_map[environment])

    model_config = SettingsConfigDict(env_file=env_file_map[environment])

    database_url: str | None = os.getenv("DATABASE_URL")
    base_url: str | None = os.getenv("BASE_URL")

    media_dir_host: pathlib.Path = pathlib.Path("/media")

    if environment == "dev":
        # NOTE: dev environment uses paths in containers
        base_dir: pathlib.Path = pathlib.Path(__file__).resolve().parents[1]
        static_dir: pathlib.Path = base_dir / "static"
        media_dir_local: pathlib.Path = base_dir / "static/media"

    elif environment == "test":
        # NOTE: test environment uses paths locally except the database
        base_dir: pathlib.Path = pathlib.Path(__file__).resolve().parents[2]
        static_dir: pathlib.Path = base_dir / "client/static"
        media_dir_local: pathlib.Path = base_dir / "tests/media/test_result"


@lru_cache
def get_settings() -> Settings:
    logger.info("Loading configuration...")
    return Settings()

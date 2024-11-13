import asyncio
import logging
import os
from typing import Generator

import pytest_asyncio
from faker import Faker
from httpx import ASGITransport, AsyncClient
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from project.server.main import database
from project.server.main.app import create_app
from project.server.main.config import Settings, get_settings
from project.server.main.database import FollowRelation, Like, Tweet, User

logger_test = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

logging.getLogger("faker").setLevel(logging.ERROR)


@pytest_asyncio.fixture(scope="session", autouse=True)
def set_env():
    os.environ["ENVIRONMENT"] = "test"
    os.environ["TESTING"] = "True"


settings: Settings = get_settings()
async_engine = create_async_engine(
    url=settings.database_url, echo=True, poolclass=NullPool
)  # use NullPool to avoid stuck of running several requests


# drop all database every time when test complete
@pytest_asyncio.fixture(scope="session")
async def async_db_engine():
    logger_test.info("Start create database engine..")

    async with async_engine.begin() as conn:
        await conn.run_sync(database.Base.metadata.drop_all)
        await conn.run_sync(database.Base.metadata.create_all)
        logger_test.info("Database engine created with url: %s", settings.database_url)
    yield async_engine
    async with async_engine.begin() as conn:
        await conn.run_sync(database.Base.metadata.drop_all)


# truncate all table to isolate tests
@pytest_asyncio.fixture(scope="session")
async def async_db(async_db_engine: AsyncEngine):
    async_session = async_sessionmaker(
        expire_on_commit=False,
        autoflush=False,
        bind=async_db_engine,
        class_=AsyncSession,
    )

    logger_test.info("Start async_session..")

    async with async_session() as _session:
        # await session.begin()
        yield _session

        logger_test.info("Close async_session..")
        # await _session.rollback()
        #
        # for table in reversed(database.Base.metadata.sorted_tables):
        #     await session.execute(text(f"TRUNCATE {table.name} CASCADE;"))
        # await session.commit()
        # for table in database.Base.metadata.tables:
        #     await session.execute(text(f"TRUNCATE TABLES {table} CASCADE;"))
        # await session.commit()


# test client
@pytest_asyncio.fixture(scope="session")
async def async_client(async_db_engine: AsyncEngine) -> AsyncClient:
    logger_test.info("Start test app..")
    async with AsyncClient(
        transport=ASGITransport(app=create_app()), base_url=settings.base_url
    ) as client:
        yield client


# This gives extra warnings:
@pytest_asyncio.fixture(scope="session")
def event_loop() -> Generator:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# fill a test data
@pytest_asyncio.fixture(scope="session")
async def async_db_dummy_fill(async_db: AsyncSession) -> None:
    fake = Faker()
    users = [
        User(api_key="test1", name=fake.name()),
        User(api_key="test2", name=fake.name()),
        User(api_key="test3", name=fake.name()),
    ]

    users[0].tweets_of_user.extend(
        [
            Tweet(
                content=fake.text(5),
                attachments=[],
                author=1,
            ),
            Tweet(
                content=fake.text(5),
                attachments=[],
                author=1,
            ),
            Tweet(
                content=fake.text(5),
                attachments=[],
                author=1,
            ),
        ]
    )

    users[1].tweets_of_user.extend(
        [
            Tweet(
                content=fake.text(5),
                attachments=[],
                author=2,
            ),
            Tweet(
                content=fake.text(5),
                attachments=[],
                author=2,
            ),
            Tweet(
                content=fake.text(5),
                attachments=[],
                author=2,
            ),
        ]
    )
    users[2].tweets_of_user.extend(
        [
            Tweet(
                content=fake.text(5),
                attachments=[],
                author=2,
            ),
            Tweet(
                content=fake.text(5),
                attachments=[],
                author=2,
            ),
            Tweet(
                content=fake.text(5),
                attachments=[],
                author=2,
            ),
        ]
    )

    users[0].likes_of_user.extend(
        [
            Like(
                follower_id=1,
                tweet_id=4,
            ),
            Like(
                follower_id=1,
                tweet_id=5,
            ),
        ]
    )

    users[1].likes_of_user.extend(
        [
            Like(
                follower_id=2,
                tweet_id=1,
            ),
            Like(
                follower_id=2,
                tweet_id=2,
            ),
            Like(
                follower_id=2,
                tweet_id=3,
            ),
        ]
    )

    users[2].likes_of_user.extend(
        [
            Like(
                follower_id=3,
                tweet_id=2,
            ),
            Like(
                follower_id=3,
                tweet_id=6,
            ),
        ]
    )
    users[0].following_to.extend(
        [
            FollowRelation(
                follower_id=1,
                following_id=2,
            ),
        ]
    )
    users[2].following_to.extend(
        [
            FollowRelation(
                follower_id=3,
                following_id=2,
            ),
        ]
    )

    logger_test.info("!!! Start creating fake data in test database..")
    async_db.add_all(users)
    await async_db.commit()
    logger_test.info("!!! Finish creating fake data in test database..")
    return None

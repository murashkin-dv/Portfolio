import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from project.server.main.config import logger
from project.server.main.database import Tweet

pytestmark = pytest.mark.asyncio


@pytest.mark.tweets
async def test_api_get_tweets_positive(
    async_client: AsyncClient, async_db: AsyncSession, async_db_dummy_fill: None
) -> None:
    """
    Test for get tweet feed for current user
    """
    users = ["test1", "test2"]
    for i_user in users:
        tweets = await Tweet.get_tweets(async_db, i_user)
        response = await async_client.get("/api/tweets", headers={"api-key": i_user})
        # to match response schema:
        for i_tweet in tweets["tweets"]:
            i_tweet.pop("date_tweet")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == tweets


@pytest.mark.tweets
async def test_api_create_tweet_positive(
    async_client: AsyncClient, async_db: AsyncSession, async_db_dummy_fill: None
) -> None:
    """
    Test for create tweet by current user
    """
    user = "test1"
    data = {"tweet_data": "Hello, I am test1.", "tweet_media_ids": None, "author": 1}

    response = await async_client.post(
        "/api/tweets", headers={"api-key": user}, json=data
    )

    tweet_id_expect_query = await async_db.execute(
        select(func.count()).select_from(Tweet)
    )
    tweet_id_expect = tweet_id_expect_query.scalar()

    response_expect = {"result": True, "tweet_id": tweet_id_expect}

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == response_expect


@pytest.mark.tweets
async def test_api_delete_tweet_positive(
    async_client: AsyncClient, async_db: AsyncSession, async_db_dummy_fill: None
) -> None:
    """
    Test for delete tweet created by current user
    """
    user = "test1"
    author = 1
    tweet_id_delete_query = await async_db.execute(
        select(Tweet.id).where(Tweet.author == author)
    )
    tweet_id_delete = tweet_id_delete_query.scalars().first()

    response = await async_client.delete(
        f"/api/tweets/{tweet_id_delete}", headers={"api-key": user}
    )

    response_expect = {"result": tweet_id_delete}

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == response_expect


@pytest.mark.tweets
async def test_api_delete_tweet_not_found_negative(
    async_client: AsyncClient, async_db: AsyncSession, async_db_dummy_fill: None
) -> None:
    """
    Test for delete tweet which is not found
    """
    user = "test1"

    tweet_id_delete_wrong_query = await async_db.execute(
        select(func.count()).select_from(Tweet)
    )
    tweet_id_delete_wrong = tweet_id_delete_wrong_query.scalar()
    if tweet_id_delete_wrong is not None:
        tweet_id_delete_wrong += 10
    logger.info("!!! Tweet Wrong: %s", tweet_id_delete_wrong)
    response = await async_client.delete(
        f"/api/tweets/{tweet_id_delete_wrong}", headers={"api-key": user}
    )

    response_expect = {
        "error_message": "Tweet not found",
        "error_type": "N/A",
        "result": False,
    }

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == response_expect


@pytest.mark.tweets
async def test_api_delete_tweet_wrong_user_negative(
    async_client: AsyncClient, async_db: AsyncSession, async_db_dummy_fill: None
) -> None:
    """
    Test for delete tweet with id created by other user
    """
    user = "test1"
    author = 1
    tweet_id_delete_wrong_query = await async_db.execute(
        select(Tweet.id).where(Tweet.author != author)
    )
    tweet_id_delete_wrong = tweet_id_delete_wrong_query.scalars().first()
    response = await async_client.delete(
        f"/api/tweets/{tweet_id_delete_wrong}", headers={"api-key": user}
    )

    response_expect = {
        "error_message": "User does not have a permission to remove the tweet",
        "error_type": "N/A",
        "result": False,
    }

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == response_expect

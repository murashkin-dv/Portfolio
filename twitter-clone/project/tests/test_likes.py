import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

pytestmark = pytest.mark.asyncio


@pytest.mark.likes
async def test_api_create_like_positive(
    async_client: AsyncClient, async_db: AsyncSession, async_db_dummy_fill: None
) -> None:
    """
    Test for create like for a tweet id created by other user
    """
    user = "test1"
    tweet_id = 6
    response = await async_client.post(
        f"/api/tweets/{tweet_id}/likes", headers={"api-key": user}
    )

    response_expect = {"result": True}

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == response_expect


@pytest.mark.likes
async def test_api_create_like_negative(
    async_client: AsyncClient, async_db: AsyncSession, async_db_dummy_fill: None
) -> None:
    """
    Test for create like for a tweet id owned by current user
    """
    user = "test1"
    tweet_id = 1

    response = await async_client.post(
        f"/api/tweets/{tweet_id}/likes", headers={"api-key": user}
    )

    response_expect = {"result": False}

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == response_expect


@pytest.mark.likes
async def test_api_delete_like_positive(
    async_client: AsyncClient, async_db: AsyncSession, async_db_dummy_fill: None
) -> None:
    """
    Test for delete like created by current user
    """
    user = "test1"
    tweet_id_delete = 4

    response = await async_client.delete(
        f"/api/tweets/{tweet_id_delete}/likes", headers={"api-key": user}
    )

    response_expect = {"result": True}

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == response_expect

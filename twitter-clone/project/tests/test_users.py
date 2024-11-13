import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from project.server.main.database import User

pytestmark = pytest.mark.asyncio


@pytest.mark.users
async def test_api_users_me_positive(
    async_client: AsyncClient, async_db: AsyncSession, async_db_dummy_fill: None
) -> None:
    """
    Test for getting data by api-key for current user
    """
    users = ["test1", "test2"]
    for i_user in users:
        user = await User().get_user_by_apikey(async_db, i_user)
        response = await async_client.get("/api/users/me", headers={"api-key": i_user})

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == user


@pytest.mark.users
async def test_api_users_me_negative(
    async_client: AsyncClient, async_db: AsyncSession, async_db_dummy_fill: None
) -> None:
    """
    Test for getting data by api-key for unregistered user
    """
    unregistered_user = "test100"
    response = await async_client.get(
        "/api/users/me", headers={"api-key": unregistered_user}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "result": False,
        "error_type": "N/A",
        "error_message": "User not found.",
    }


@pytest.mark.users
async def test_api_users_by_id_positive(
    async_client: AsyncClient, async_db: AsyncSession, async_db_dummy_fill: None
) -> None:
    """
    Test for getting data by user id
    """
    user_id = [1, 2]
    for i_user_id in user_id:
        user_by_id = await User().get_user_by_id(async_db, i_user_id)
        # modification to match response schema:
        user_by_id["user"].pop("api_key", None)
        user_by_id["user"].pop("date_of_registration", None)
        response = await async_client.get(f"/api/users/{i_user_id}")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == user_by_id


@pytest.mark.users
async def test_api_users_by_id_negative(
    async_client: AsyncClient, async_db: AsyncSession, async_db_dummy_fill: None
) -> None:
    """
    Test for getting data by unregistered user id
    """
    # user id missing test
    unregistered_user_id = 10
    response = await async_client.get(f"/api/users/{unregistered_user_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND

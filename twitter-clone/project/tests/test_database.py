import datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from project.server.main.database import User
from project.server.main.error_handler import ObjectNotFoundException

pytestmark = pytest.mark.asyncio


@pytest.mark.database
async def test_dummy_insert_positive(
    async_client: AsyncClient, async_db: AsyncSession, async_db_dummy_fill: None
) -> None:
    """
    Test for filling database with dummy data
    """

    users = ["test1", "test2"]
    for i_user in users:
        user_query = await async_db.execute(select(User).where(User.api_key == i_user))
        user = user_query.fetchone()[0]

        assert user.api_key == i_user
        assert user.date_of_registration == datetime.datetime.now().date()


@pytest.mark.database
async def test_get_current_user_by_apikey_positive(
    async_client: AsyncClient, async_db: AsyncSession, async_db_dummy_fill: None
) -> None:
    """
    Test for getting user by api key
    """

    user_api = "test1"
    user_query = await async_db.execute(select(User).where(User.api_key == user_api))
    user = user_query.fetchone()[0]

    assert user.api_key == user_api
    assert user.date_of_registration == datetime.datetime.now().date()


@pytest.mark.database
async def test_get_current_user_by_apikey_negative(
    async_client: AsyncClient, async_db: AsyncSession, async_db_dummy_fill: None
) -> None:
    """
    Test for getting user by api key which does not exist
    """
    user_api = "abc"
    with pytest.raises(ObjectNotFoundException):
        await User.get_current_user(async_db, user_api)


@pytest.mark.database
async def test_get_user_by_id_positive(
    async_client: AsyncClient, async_db: AsyncSession, async_db_dummy_fill: None
) -> None:
    """
    Test for getting user by user id
    """

    user_id = 1
    user_query = await async_db.execute(select(User).where(User.id == user_id))
    user = user_query.fetchone()[0]

    assert user.id == user_id
    assert user.date_of_registration == datetime.datetime.now().date()


@pytest.mark.database
async def test_get_user_by_id_negative(
    async_client: AsyncClient, async_db: AsyncSession, async_db_dummy_fill: None
) -> None:
    """
    Test for getting user by user id which does not exist
    """

    user_id = 10
    with pytest.raises(ObjectNotFoundException):
        await User.get_user_by_id(async_db, user_id)

import pytest
from httpx import AsyncClient
from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from project.server.main.database import FollowRelation, User

pytestmark = pytest.mark.asyncio


@pytest.mark.follows
async def test_api_create_follows_positive(
    async_client: AsyncClient, async_db: AsyncSession, async_db_dummy_fill: None
) -> None:
    """
    Test for creating follows relation
    """
    user = "test1"
    follower_user = await User().get_current_user(async_db, user)
    following_id = 2
    response = await async_client.post(
        f"/api/users/{following_id}/follow", headers={"api-key": user}
    )

    new_follow_query = await async_db.execute(
        select(FollowRelation.id).filter(
            and_(
                FollowRelation.follower_id == follower_user.id,
                FollowRelation.following_id == following_id,
            )
        )
    )

    new_follow = new_follow_query.scalar()
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {"result": new_follow}


@pytest.mark.follows
async def test_api_delete_follows_positive(
    async_client: AsyncClient, async_db: AsyncSession, async_db_dummy_fill: None
) -> None:
    """
    Test for deleting follows relation
    """
    user = "test1"
    follower = await User().get_current_user(async_db, user)
    following_id = 2
    response = await async_client.delete(
        f"/api/users/{following_id}/follow", headers={"api-key": user}
    )

    await async_db.execute(
        delete(FollowRelation).filter(
            and_(
                FollowRelation.follower_id == follower.id,
                FollowRelation.following_id == following_id,
            )
        )
    )
    await async_db.commit()
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"result": True}


@pytest.mark.follows
async def test_api_delete_follows_negative(
    async_client: AsyncClient, async_db: AsyncSession, async_db_dummy_fill: None
) -> None:
    """
    Test for deleting follows relation
    """
    user = "test1"
    follower = await User().get_current_user(async_db, user)
    following_id = 3
    response = await async_client.delete(
        f"/api/users/{following_id}/follow", headers={"api-key": user}
    )

    await async_db.execute(
        delete(FollowRelation).filter(
            and_(
                FollowRelation.follower_id == follower.id,
                FollowRelation.following_id == following_id,
            )
        )
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "error_message": "User does not follow this user",
        "error_type": "N/A",
        "result": False,
    }

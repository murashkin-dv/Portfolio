import pathlib

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST

from project.server.main.database import Media

pytestmark = pytest.mark.asyncio


@pytest.mark.likes
async def test_api_create_media_file_check_positive(
    async_client: AsyncClient, async_db: AsyncSession
) -> None:
    """
    Test for media file check (single file only):
    size not to exceed 2Mb,
    format is [jped, png, gif]
    """
    user = "test1"

    file_ok = pathlib.Path(__file__).parent / "media/image_ok.jpg"

    with open(file_ok, "r+b") as file:
        files = {"file": file}
        response = await async_client.post(
            "/api/medias", headers={"api-key": user}, files=files
        )
    media_id_expect_query = await async_db.execute(
        select(func.count()).select_from(Media)
    )
    media_id_expect = media_id_expect_query.scalar()

    assert response.status_code == HTTP_201_CREATED
    assert response.json() == {"result": True, "media_id": media_id_expect}


@pytest.mark.likes
async def test_api_create_media_file_check_size_negative(
    async_client: AsyncClient, async_db: AsyncSession
) -> None:
    """
    Test for media file check (single file only): wrong size
    """
    user = "test1"

    file_large = pathlib.Path(__file__).parent / "media/image_large.jpg"

    with open(file_large, "r+b") as file:
        files = {"file": file}
        response = await async_client.post(
            "/api/medias", headers={"api-key": user}, files=files
        )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "File is too large (over 2Mb)"}


@pytest.mark.media
async def test_api_create_media_file_check_type_negative(
    async_client: AsyncClient, async_db: AsyncSession
) -> None:
    """
    Test for media file check (single file only): wrong type
    """
    user = "test1"

    file_other = pathlib.Path(__file__).parent / "media/image_other.txt"

    with open(file_other, "r+b") as file:
        files = {"file": file}
        response = await async_client.post(
            "/api/medias", headers={"api-key": user}, files=files
        )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Invalid file type"}

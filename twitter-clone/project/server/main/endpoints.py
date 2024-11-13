from typing import Annotated, Any, List

from fastapi import Body, Depends, Header, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.status import HTTP_200_OK, HTTP_201_CREATED

from . import schemas
from .app import media_dir_host, media_dir_local, router, templates
from .config import Settings, get_settings, logger
from .database import FollowRelation, Like, Media, Tweet, User, get_session
from .error_handler import ObjectNotFoundException


# Endpoints creation
@router.get("/", response_class=HTMLResponse, tags=["Log In"])
@router.get("/login", response_class=HTMLResponse, tags=["Log In"])
async def get_page_template(
    _request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
):
    """
    Login page
    """

    logger.info("Start Login..")
    return templates.TemplateResponse("index.html", {"request": _request})


@router.get(
    "/api/users/me",
    response_model=schemas.UserResponseModel,
    responses=schemas.responses,
    tags=["Users"],
)
async def get_current_user_info(
    api_key: Annotated[str, Header()],
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    _session: AsyncSession = Depends(get_session),
) -> Any:
    """
    Get current user's profile
    """

    logger.info("Extracting my profile..")
    user_api_key = request.headers.get("api-key")
    user_by_api = await User.get_user_by_apikey(_session, user_api_key)
    logger.info("Extracting my profile.. Success!")
    return user_by_api


@router.get(
    "/api/users/{user_id}",
    response_model=schemas.UserResponseModel,
    responses=schemas.responses,
    tags=["Users"],
)
async def get_user_info_by_id(
    user_id: int,
    settings: Annotated[Settings, Depends(get_settings)],
    _session: AsyncSession = Depends(get_session),
) -> Any:
    """
    Get a user's profile by user_id
    """
    logger.info("Extracting user profile by ID..")
    user_by_id = await User.get_user_by_id(_session, user_id)
    logger.info("Extracting user profile by ID.. Success")
    return user_by_id


@router.post(
    "/api/tweets",
    response_model=schemas.TweetCreateResponseModel,
    responses=schemas.responses,
    status_code=HTTP_201_CREATED,
    tags=["Tweets"],
)
async def create_tweet(
    api_key: Annotated[str, Header()],
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    tweet_data: Annotated[str, Body()],
    tweet_media_ids: Annotated[List[int] | None, Body()] = None,
    _session: AsyncSession = Depends(get_session),
) -> dict[Any, Any]:
    """
    Create a new tweet
    """
    logger.info("Creating a new tweet")
    try:
        user_api_key = request.headers.get("api-key")
    except ObjectNotFoundException:
        raise ObjectNotFoundException(error_message="User not found.")
    tweet_data = await request.json()
    new_tweet_id = await Tweet.create_tweet(_session, user_api_key, tweet_data)  # type: ignore
    response_data = {"result": True, "tweet_id": new_tweet_id}
    logger.info("Creating a new tweet.. Success!")
    return response_data


@router.get(
    "/api/tweets",
    response_model=schemas.TweetResponseModel,
    responses=schemas.responses,
    tags=["Tweets"],
)
async def get_tweets(
    api_key: Annotated[str, Header()],
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    _session: AsyncSession = Depends(get_session),
) -> Any:
    """
    Get a list of tweets for current user
    """
    logger.info("Extracting tweets..")
    user_api_key = request.headers["api-key"]
    tweets_all = await Tweet.get_tweets(_session, user_api_key)
    logger.info("Extracting tweets.. Success!")
    return tweets_all


@router.delete("/api/tweets/{tweet_id}", responses=schemas.responses, tags=["Tweets"])
async def delete_tweet(
    api_key: Annotated[str, Header()],
    tweet_id: int,
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    _session: AsyncSession = Depends(get_session),
) -> dict:
    """
    Delete a tweet by id
    """
    logger.info("Deleting tweet id %s..", tweet_id)
    user_api_key = request.headers["api-key"]
    tweet_delete = await Tweet.delete_tweet(_session, user_api_key, tweet_id)
    logger.info("Deleting tweet.. Success!")
    return {"result": tweet_delete}


@router.post(
    "/api/medias",
    status_code=HTTP_201_CREATED,
    responses=schemas.responses,
    tags=["Tweets"],
)
async def upload_media(
    api_key: Annotated[str, Header()],
    request: Request,
    file: UploadFile,
    settings: Annotated[Settings, Depends(get_settings)],
    _session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """
    Upload a media file to tweet
    """
    logger.info("Uploading media..")
    user_api_key = request.headers["api-key"]
    new_media = Media()
    await new_media.check_file(_session, file)
    file_id = await new_media.process_file(
        user_api_key, _session, media_dir_host, media_dir_local, file
    )
    return {"result": True, "media_id": file_id}


@router.post(
    "/api/tweets/{tweet_id}/likes",
    response_model=None,
    responses=schemas.responses,
    status_code=HTTP_201_CREATED,
    tags=["Likes"],
)
async def create_like(
    api_key: Annotated[str, Header()],
    tweet_id: int,
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    _session: AsyncSession = Depends(get_session),
) -> RedirectResponse | dict[str, Any]:
    """
    Create a like for the tweet with id
    """
    user_api_key = request.headers["api-key"]
    logger.info("Create like for tweet %s..", tweet_id)
    new_like = await Like.create_like(_session, user_api_key, tweet_id)
    if new_like:
        logger.info("Create like.. Success!")
    else:
        logger.info("Create like.. Fail! Like personal tweets is not allowed")
    return {"result": new_like}


@router.delete(
    "/api/tweets/{tweet_id}/likes",
    status_code=HTTP_200_OK,
    responses=schemas.responses,
    tags=["Likes"],
)
async def delete_like(
    api_key: Annotated[str, Header()],
    tweet_id: int,
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    _session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """
    Delete a like by tweet id
    """
    logger.info("Deleting like for tweet id %s..", tweet_id)
    user_api_key = request.headers["api-key"]
    like_delete = await Like.delete_like(_session, user_api_key, tweet_id)
    logger.info("Deleting like.. Success!")
    return {"result": like_delete}


@router.post(
    "/api/users/{user_id}/follow",
    response_model=None,
    responses=schemas.responses,
    status_code=HTTP_201_CREATED,
    tags=["Follows"],
)
async def create_follow(
    api_key: Annotated[str, Header()],
    user_id: int,
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    _session: AsyncSession = Depends(get_session),
) -> RedirectResponse | dict[str, Any]:
    """
    Create a follow mark for the user with id
    """
    user_api_key = request.headers["api-key"]
    logger.info("Did user follow the user %s already?..", user_id)
    logger.info("Following the user %s..", user_id)
    new_follow = await FollowRelation.create_follow(_session, user_api_key, user_id)
    logger.info("Following the user.. Success!")
    return {"result": new_follow}


@router.delete(
    "/api/users/{user_id}/follow", responses=schemas.responses, tags=["Follows"]
)
async def delete_follow(
    api_key: Annotated[str, Header()],
    user_id: int,
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    _session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """
    Delete a follow to a user id
    """
    logger.info("Deleting follow to user id %s..", user_id)
    user_api_key = request.headers["api-key"]
    follow_delete = await FollowRelation.delete_follow(_session, user_api_key, user_id)
    logger.info("Deleting follow.. Success!")
    return {"result": follow_delete}

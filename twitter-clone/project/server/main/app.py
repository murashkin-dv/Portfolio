import logging
import os
from contextlib import asynccontextmanager
from http.client import HTTPException
from typing import Annotated, Any, List

from fastapi import APIRouter, Body, Depends, FastAPI, Header, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse, RedirectResponse

from . import database, schemas
from .config import Settings, get_settings
from .database import (
    FollowRelation,
    Like,
    Media,
    Tweet,
    User,
    async_session,
    engine,
    insert_data,
    session,
)
from .error_handler import ObjectNotFoundException, ServerException, SQLAlchemyException
from .schemas import TweetResponseModel


def create_app() -> FastAPI:
    """Initialize the core application."""

    # setting environment - should work for development by default
    # os.environ["FASTAPI_ENV"] = "development"
    settings: Settings = get_settings()

    static_dir = os.path.join(settings.base_dir, "static")
    media_dir_local = os.path.join(settings.base_dir, "static", "media")
    media_dir_host = os.path.normpath("/media")

    # Initialize logging
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("faker").setLevel(logging.ERROR)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        # On startup: check whether database exists and create if required
        logger.info("!!! Checking if the database exists..")
        async with engine.begin() as conn:
            tables = await conn.run_sync(
                lambda sync_conn: inspect(sync_conn).get_table_names()
            )

        if "users" in tables:
            logger.info("Database exists. Continue from docker volume.")
        else:
            logger.info("!!! Database does not exist. Creating initial database..")
            async with engine.begin() as conn:
                # await conn.run_sync(database.Base.metadata.drop_all)
                await conn.run_sync(database.Base.metadata.create_all)
            await insert_data(async_session)
            logger.info("!!! Database has been created successfully. ")

        yield
        # On shutdown: clean up and release the resources
        await session.close()
        await engine.dispose()

    app = FastAPI(
        lifespan=lifespan,
        title="Tweet-Clone",
        version="1.0.0",
        description="https://localhost:8080",
        docs_url="/docs",
        openapi_url="/openapi.json",  #
        redoc_url=None,  # Disable redoc documents
    )
    app.add_middleware(
        CORSMiddleware,  # type: ignore
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.mount(static_dir, StaticFiles(directory="static"), name="static")
    templates = Jinja2Templates(directory="static")

    router = APIRouter()

    # Dependency to create future sessions for us on demand
    async def get_session() -> AsyncSession:  # type: ignore
        async with async_session() as _session:
            yield _session

    # Exception handlers
    @app.exception_handler(ObjectNotFoundException)
    async def user_not_found_exception_handler(
        request: Request, exc: ObjectNotFoundException
    ):
        logger.error("User not found error: %s", exc)
        return JSONResponse(
            status_code=404,
            content={
                "result": exc.result,
                "error_type": exc.error_type,
                "error_message": exc.error_message,
            },
        )

    @app.exception_handler(ServerException)
    async def server_exception_handler(request: Request, exc: ServerException):
        logger.error("Unhandled server error: %s", exc)
        return JSONResponse(
            status_code=500,
            content={
                "result": exc.result,
                "error_type": exc.error_type,
                "error_message": exc.error_message,
            },
        )

    @app.exception_handler(SQLAlchemyException)
    async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyException):
        logger.error("SQLAlchemy error: %s", exc.error_message)
        return JSONResponse(
            status_code=500,
            content={
                "result": False,
                "error_type": str(type(exc)),
                "error_message": exc.error_message,
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled error: %s", exc)
        return JSONResponse(
            status_code=500,
            content={
                "result": False,
                "error_type": str(type(exc)),
                "error_message": str(exc),
            },
        )

    # Endpoints creation
    @router.get("/", response_class=HTMLResponse, tags=["Log In"])
    @router.get("/login", response_class=HTMLResponse, tags=["Log In"])
    async def get_page_template(
        _request: Request,
        settings: Annotated[Settings, Depends(get_settings)],
    ):
        """Login page"""
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
        try:
            user_api_key = request.headers.get("api-key")
        except HTTPException:
            raise HTTPException
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
        status_code=status.HTTP_201_CREATED,
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
        except HTTPException:
            raise HTTPException
        tweet_data = await request.json()
        new_tweet_id = await Tweet.create_tweet(_session, user_api_key, tweet_data)  # type: ignore
        response_data = {"result": True, "tweet_id": new_tweet_id}
        logger.info("Creating a new tweet.. Success!")
        return response_data

    @router.get(
        "/api/tweets",
        response_model=TweetResponseModel,
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

    @router.delete(
        "/api/tweets/{tweet_id}", responses=schemas.responses, tags=["Tweets"]
    )
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
        status_code=status.HTTP_201_CREATED,
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
        status_code=status.HTTP_201_CREATED,
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
        status_code=status.HTTP_200_OK,
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
        status_code=status.HTTP_201_CREATED,
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
        logger.info("Deleting follow to user id %c..", user_id)
        user_api_key = request.headers["api-key"]
        follow_delete = await FollowRelation.delete_follow(
            _session, user_api_key, user_id
        )
        logger.info("Deleting follow.. Success!")
        return {"result": follow_delete}

    app.include_router(router)

    return app


# app = create_app()

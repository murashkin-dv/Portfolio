import logging
import os
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import inspect
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from . import database
from .config import Settings, get_settings
from .database import async_session, engine, insert_data, session
from .error_handler import ObjectNotFoundException, ServerException, SQLAlchemyException

# setting environment
os.environ["ENVIRONMENT"] = "dev"

settings: Settings = get_settings()
static_dir = settings.static_dir
media_dir_local = settings.media_dir_local
media_dir_host = settings.media_dir_host

# Initialize logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("faker").setLevel(logging.ERROR)

templates = Jinja2Templates(directory="static")

router = APIRouter()


def create_app() -> FastAPI:
    """
    Initialize the core application.
    """

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        # On startup: check whether database exists and create if required
        logger.info("!!! Checking if the database exists..")
        async with engine.begin() as conn:
            tables = await conn.run_sync(
                lambda sync_conn: inspect(sync_conn).get_table_names()
            )

        if "users" in tables:
            logger.info("!!! Database exists. Continue from docker volume.")
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

    _app = FastAPI(
        lifespan=lifespan,
        title="Tweet-Clone",
        version="1.0.0",
        description=settings.base_url,
        docs_url="/docs",
        openapi_url="/openapi.json",  #
        redoc_url=None,  # Disable redoc documents
    )
    _app.add_middleware(
        CORSMiddleware,  # type: ignore
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    _app.mount(str(static_dir), StaticFiles(directory=str(static_dir)), name="static")

    _app.include_router(router)

    # Exception handlers
    @_app.exception_handler(ObjectNotFoundException)
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

    @_app.exception_handler(ServerException)
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

    @_app.exception_handler(SQLAlchemyException)
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

    @_app.exception_handler(Exception)
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

    return _app

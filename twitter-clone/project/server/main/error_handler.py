from typing import Type

from sqlalchemy.exc import SQLAlchemyError


class AppException(Exception):
    def __init__(
        self,
        error_type: (
            str | TypeError | SQLAlchemyError | Type[SQLAlchemyError]
        ) = "Unknown type",
        error_message: str = "Something has happened..",
    ):
        self.result = False
        self.error_type = error_type
        self.error_message = error_message


class ObjectNotFoundException(AppException):
    def __init__(
        self,
        error_type: str = "N/A",
        error_message: str = "Requested object not found",
    ):
        super().__init__()
        self.error_type = error_type
        self.error_message = error_message


class ServerException(AppException):
    pass


class SQLAlchemyException(AppException):
    pass


# @app.exception_handler(UserNotFoundException)
# async def user_not_found_exception_handler(
#     request: Request, exc: UserNotFoundException
# ):
#     logger.error(f"User not found error: {exc}")
#     return JSONResponse(
#         status_code=404,
#         content={
#             "result": exc.result,
#             "error_type": exc.error_type,
#             "error_message": exc.error_message,
#         },
#     )
#
#
# @app.exception_handler(ServerException)
# async def server_exception_handler(request: Request, exc: ServerException):
#     logger.error(f"Unhandled server error: {exc}")
#     return JSONResponse(
#         status_code=500,
#         content={
#             "result": exc.result,
#             "error_type": exc.error_type,
#             "error_message": exc.error_message,
#         },
#     )
#
#
# @app.exception_handler(SQLAlchemyException)
# async def server_exception_handler(request: Request, exc: SQLAlchemyException):
#     logger.error(f"Unhandled SQLAlchemy error: {exc}")
#     return JSONResponse(
#         status_code=500,
#         content={
#             "result": exc.result,
#             "error_type": exc.error_type,
#             "error_message": exc.error_message,
#         },
#     )


# Example:
# @app.get("/unicorns/{name}")
# async def read_unicorn(name: str):
#     if name == "yolo":
#         raise UnicornException(name=name)
#     return {"unicorn_name": name}

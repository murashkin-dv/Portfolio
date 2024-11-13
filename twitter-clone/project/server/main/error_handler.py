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

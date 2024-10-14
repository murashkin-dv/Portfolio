import datetime

from peewee import (
    CharField,
    DateTimeField,
    ForeignKeyField,
    IntegerField,
    Model,
    PrimaryKeyField,
    Proxy
)


proxy = Proxy()


class BaseModel(Model):
    id = PrimaryKeyField(unique=True)


    class Meta:
        database = proxy
        order_by = "created_at"


class UserData(BaseModel):
    created_at = DateTimeField(
            default=datetime.datetime.now().isoformat(sep=" ",
                                                      timespec="seconds")
    )
    from_user_id = IntegerField()
    nickname = CharField(null=True)
    firstname = CharField(null=True)
    lastname = CharField(null=True)
    age = CharField(null=True)
    moto_experience = CharField(null=True)


    class Meta:
        db_table = "Active Users"


class UserMessageLog(BaseModel):
    created_at = DateTimeField(
            default=datetime.datetime.now().isoformat(sep=" ",
                                                      timespec="seconds")
    )
    from_user_id = ForeignKeyField(UserData)
    user_message = CharField()


    class Meta:
        db_table = "Message Log for a User"


class DataBaseCRUD:
    """
    Class performs a basic actions with an active database:
        - new user check
        - log a user data like age, motorcycle driving experience
        - log a message from a user
        - TBD
    """

    @staticmethod
    def new_user_check(user_id: int) -> bool:
        """
        Method checks whether a new user has been registered in database
        already.
        :param user_id: int
        :return: bool
        """
        # with self.active_db as data:
        if UserData.get_or_none(from_user_id=user_id):
            return True
        else:
            return False

    @staticmethod
    def log_user(user_id: int,
                 u_nickname: str = None,
                 u_firstname: str = None,
                 u_lastname: str = None,
                 u_age: str = None,
                 u_moto_exp: str = None) -> None:
        """
        A method logs user's name, age, moto experience into a database table
        UserData

        :param user_id: from_user.id object from pyTelegramBotAPI
        :param u_nickname: str
        :param u_firstname: str
        :param u_lastname: str
        :param u_age: str
        :param u_moto_exp: str
        :return: none
        """

        if not (u_nickname or
                u_firstname or
                u_lastname or
                u_age or
                u_moto_exp):
            UserData.create(
                    from_user_id=user_id)
        else:
            (UserData.update(
                    nickname=u_nickname,
                    firstname=u_firstname,
                    lastname=u_lastname,
                    age=u_age,
                    moto_experience=u_moto_exp)
             .where(UserData.from_user_id == user_id)
             .execute())

    @staticmethod
    def log_message(user_id: int,
                    message: str) -> None:
        """
        A method logs user's messages into the database table UserMessageLog

        :param user_id: from_user.id object from pyTelegramBotApi
        :param message: str
        :return: none
        """

        UserMessageLog.create(
                from_user_id=user_id,
                user_message=message,
        )

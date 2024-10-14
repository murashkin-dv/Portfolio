from telebot.handler_backends import State, StatesGroup


class UserInfoState(StatesGroup):
    """
    Class describes user states and requests, logs data about a user.

    age: registers an age of user
    moto_driving_experience: registers user's driving experience on
    a motorcycle (assume driving experience could start at the
    age of 16 and should be less than the user's age accordingly)
    """

    age = State()
    moto_driving_experience = State()

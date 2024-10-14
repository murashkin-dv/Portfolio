from telebot.types import Message

from database.database import DataBaseCRUD
from loader import bot
from states.contact_info import UserInfoState


@bot.message_handler(commands=["start"])
def bot_start(message: Message) -> None:
    """
    Function initiates Class DataBaseCRUD and requests a user's age.
    :param message: incoming message from a user
    :return: None
    """

    if DataBaseCRUD.new_user_check(message.from_user.id):
        bot.send_message(message.from_user.id,
                         'Бот уже запущен. Введите другую команду или '
                         'воспользуйтесь командой /help.')
        bot.delete_state(message.from_user.id, message.chat.id)
        return
    else:
        bot.set_state(message.from_user.id, UserInfoState.age, message.chat.id)
        bot.send_message(message.from_user.id,
                         f'Здравствуйте, {message.from_user.first_name}!\n'
                         f'Данный бот позволит Вам найти детальную справочную '
                         f'информацию по различным моделям мотоциклов.')

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['from_user_id'] = message.from_user.id
            data['username'] = message.from_user.username
            if message.from_user.first_name:
                data['firstname'] = message.from_user.first_name
            else:
                data['firstname'] = "Не указано"
            if message.from_user.last_name:
                data['lastname'] = message.from_user.last_name
            else:
                data['lastname'] = "Не указана"

        # Database Updates:
        DataBaseCRUD.log_user(user_id=message.from_user.id)
        DataBaseCRUD.log_message(message.from_user.id, message.text)

    bot.send_message(message.from_user.id, 'Введите свой возраст')


@bot.message_handler(state=UserInfoState.age, is_digit=True)
def get_age(message: Message) -> None:
    """
    Function registers the Age and requests a motorcycle experience
    :param message: incoming message from a user
    :return: None
    """

    bot.set_state(message.from_user.id,
                  UserInfoState.moto_driving_experience, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['age'] = message.text

    # history log update
    DataBaseCRUD.log_message(message.from_user.id, message.text)

    bot.send_message(message.from_user.id,
                     'Введите свой опыт вождения мотоцикла, лет, '
                     'соответствующий возрасту.\n'
                     'Введите "0", если не имеете опыта.')


@bot.message_handler(state=UserInfoState.age, is_digit=False)
def get_age_wrong(message: Message) -> None:
    """
    Function filters a wrong input for an age
    :param message: incoming message from a user
    :return: None
    """
    bot.send_message(message.from_user.id,
                     'Возраст может содержать только цифры. Попробуйте '
                     'ещё раз.')


@bot.message_handler(state=UserInfoState.moto_driving_experience,
                     is_digit=True)
def get_moto_experience(message: Message) -> None:
    """
    Function registers motorcycle experience and publish a user summary data
    :param message: incoming message from a user
    :return: None
    """

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        if int(data['age']) - int(message.text) < 16 and \
                int(message.text) != 0:
            bot.send_message(message.from_user.id,
                             '! Введенный опыт не соответствует Вашему '
                             'возрасту (в России вождение на '
                             'мотоцикле разрешено с 16 лет).\n '
                             'Попробуйте ещё раз.')
            bot.set_state(message.from_user.id,
                          UserInfoState.moto_driving_experience,
                          message.chat.id)
        else:
            bot.send_message(message.from_user.id, 'Благодарю!')
            data['moto_experience'] = message.text

        msg = ("Ваши данные:\n"
               f"Ник: {data['username']}\n"
               f"Имя: {data['firstname']}\n"
               f"Фамилия: {data['lastname']}\n"
               f"Возраст, лет: {data['age']}\n"
               f"Опыт вождения мотоцикла, лет:"
               f" {data['moto_experience']}\n")
        bot.send_message(message.chat.id, msg)

    # DB Updates:
    DataBaseCRUD.log_user(user_id=message.from_user.id,
                          u_nickname=data['username'],
                          u_firstname=data['firstname'],
                          u_lastname=data['lastname'],
                          u_age=data['age'],
                          u_moto_exp=data['moto_experience'])
    DataBaseCRUD.log_message(message.from_user.id, message.text)

    msg = (f"{data['firstname']}!\n"
           f"Выберите параметры поиска мотоциклов через встроенные "
           f"команды бота.\n"
           f"Используйте команду /help, чтобы начать.")
    bot.send_message(message.chat.id, msg)
    bot.delete_state(message.from_user.id, message.chat.id)


@bot.message_handler(state=UserInfoState.moto_driving_experience,
                     is_digit=False)
def get_moto_experience(message: Message) -> None:
    """
    Function filters a motorcycle experience wrong input
    :param message: incoming message from a user
    :return: None
    """
    bot.send_message(message.from_user.id, 'Опыт вождения может '
                                           'содержать только цифры. '
                                           'Попробуйте ещё раз.')

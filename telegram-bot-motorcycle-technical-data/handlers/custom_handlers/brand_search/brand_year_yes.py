from telebot.types import Message, ReplyKeyboardRemove

from custom_requests.api_request import api_request
from database.database import DataBaseCRUD
from keyboards.inline.pagination import message_by_page
from loader import bot
from states.search_states import SearchStates


@bot.message_handler(state=SearchStates.brand_year_yes)
def brand_year_yes(message: Message) -> None:
    """
    Function registers a year and provides requested data from the server
    with year parameter "Yes".

    :param message: incoming message from a user
    :return: none
    """

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['year'] = message.text
        search_result = api_request("/v1/motorcycles",
                                    {
                                        'make': data['brand'],
                                        'year': data['year'],
                                        'offset': 0},
                                    "GET")
        data['pages'] = search_result

    if not search_result:
        bot.send_message(message.from_user.id,
                         'Такой брэнд не найден в базе.\n'
                         'Введите другое название Брэнда (и/или года).\n'
                         'Для смены режима поиска отмените текущую '
                         'команду (/cancel)',
                         reply_markup=ReplyKeyboardRemove())
        bot.set_state(message.from_user.id,
                      SearchStates.brand,
                      message.chat.id)
    else:
        message_by_page(message=message,
                        current_user_id=message.from_user.id)
        bot.set_state(message.from_user.id,
                      SearchStates.brand,
                      message.chat.id)
    # history log update
    DataBaseCRUD.log_message(message.from_user.id, message.text)

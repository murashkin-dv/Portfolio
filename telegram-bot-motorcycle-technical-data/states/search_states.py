from telebot.handler_backends import State, StatesGroup


class SearchStates(StatesGroup):
    """
    Class describes bot states while searching process

    brand: search by motorcycle brand
    brand_year_yes / brand_year_no:
        search by moto brand with / without requested year of production

    model: search by motorcycle model
    model_year_yes / model_year_no:
        search by moto model with / without requested year of production
    """

    brand = State()
    brand_year_yes = State()
    brand_year_no = State()
    model = State()
    model_year_yes = State()
    model_year_no = State()

import random

import factory  # type: ignore
import factory.fuzzy as fuzzy  # type: ignore

from main.app import db
from main.models import Client, ParkingLot


class ClientFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Client
        sqlalchemy_session = db.session

    name = factory.Faker("first_name")
    surname = factory.Faker("last_name")
    credit_card = factory.Faker("credit_card_number")
    car_number = fuzzy.FuzzyText(prefix="Номер: ", length=9)

    # Options:
    # credit_card = factory.LazyAttribute(
    #     lambda x: random.choice([factory.Faker("credit_card_number"), None])
    # )
    # car_number = factory.Faker("text", max_nb_chars=9)


class ParkingFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = ParkingLot
        sqlalchemy_session = db.session

    address = factory.Faker("address")
    # opened = factory.LazyAttribute(lambda x: random.choice([True, False]))
    opened = factory.Faker("pybool")
    count_places = factory.LazyAttribute(lambda x: random.randrange(50, 100))
    count_available_places = count_places

import datetime

import pytest

from main.app import create_app
from main.app import db as _db
from main.models import Client, ClientParking, ParkingLot


@pytest.fixture
def app():
    _app = create_app()
    _app.config["TESTING"] = True
    _app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"

    with _app.app_context():
        _db.create_all()
        clients = [
            Client(
                name="name",
                surname="surname",
                credit_card="card_number",
                car_number="AB123",
            ),
            Client(
                name="name_1",
                surname="surname_1",
                credit_card="card_number_1",
                car_number="AB123_1",
            ),
        ]
        parking = ParkingLot(
            address="address_1",
            opened=True,
            count_places=100,
            count_available_places=99,
        )
        client_parking = ClientParking(
            # id=1,
            client_id=1,
            parking_id=1,
            time_in=datetime.datetime.now(datetime.UTC),
            time_out=None,
        )
        _db.session.bulk_save_objects(clients)
        _db.session.add(parking)
        _db.session.add(client_parking)
        _db.session.commit()

        yield _app
        _db.session.close()
        _db.drop_all()


@pytest.fixture
def client(app):
    client = app.test_client()
    yield client


@pytest.fixture
def db(app):
    with app.app_context():
        yield _db

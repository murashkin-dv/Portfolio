# запуск тестов из папки hw, in terminal: pytest tests/test_flask.py (-v)
# запуск тестов с фильтром в названии: pytest -k <text>
# запуск тестов с маркерами: pytest -m <marker_name>
# регистрация маркеров - в файле pytest.ini

import time

import pytest
from sqlalchemy import Null

from main.models import ClientParking, ParkingLot


def test_create_client(client) -> None:
    client_data = {
        # "id": 1,
        "name": "name",
        "surname": "surname",
        "credit_card": "card_number",
        "car_number": "AB123_2",
    }
    resp = client.post("/clients", data=client_data)
    assert resp.status_code == 201


def test_show_client(client) -> None:
    resp = client.get("/clients")
    assert resp.status_code == 200
    assert resp.json == [
        {
            "id": 1,
            "name": "name",
            "surname": "surname",
            "credit_card": "card_number",
            "car_number": "AB123",
        },
        {
            "id": 2,
            "name": "name_1",
            "surname": "surname_1",
            "credit_card": "card_number_1",
            "car_number": "AB123_1",
        },
    ]


def test_create_parking(client) -> None:
    parking_data = {
        # "id": 1,
        "address": "address_2",
        "opened": True,
        "count_places": 5,
        "count_available_places": 5,
    }
    resp = client.post("/parkings", data=parking_data)
    assert resp.status_code == 201


@pytest.mark.parking
def test_entry_parking(client, db) -> None:
    client_id = 2
    parking_id = 1
    resp = client.post(f"/client_parkings/{client_id}/{parking_id}")
    assert resp.status_code == 201
    lot_data: db.ParkingLot = db.session.get(ParkingLot, parking_id)
    assert lot_data.count_available_places == 98
    assert lot_data.opened is True


@pytest.mark.parking
def test_exit_parking(client, db) -> None:
    time.sleep(1)

    # client exits
    client_id = 1
    parking_id = 1
    resp = client.delete(f"/client_parkings/{client_id}/{parking_id}")
    assert resp.status_code == 201
    record_data: db.ClientParking = db.session.get(ClientParking, client_id)
    assert record_data.time_out != Null
    assert record_data.time_out > record_data.time_in
    lot_data: db.ParkingLot = db.session.get(ParkingLot, parking_id)
    assert lot_data.count_available_places == 100


def test_app_config(app):
    assert not app.config["DEBUG"]
    assert app.config["TESTING"]
    assert app.config["SQLALCHEMY_DATABASE_URI"] == "sqlite://"


@pytest.mark.parametrize("route", ["/clients"])
def test_route_status_get(client, route):
    rv = client.get(route)
    assert rv.status_code == 200

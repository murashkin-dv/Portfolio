from main.models import Client, ParkingLot

from .factories import ClientFactory, ParkingFactory


def test_create_client(app, db):
    new_client = ClientFactory()
    db.session.commit()
    assert new_client.id is not None
    assert len(db.session.query(Client).all()) == 3


def test_create_parking(app, db):
    parking = ParkingFactory()
    db.session.commit()
    assert parking.id is not None
    assert len(db.session.query(ParkingLot).all()) == 2

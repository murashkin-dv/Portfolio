from typing import Any, Dict

from sqlalchemy import UniqueConstraint

from .app import db


def same_as(column_name):
    def default_function(context):
        return context.get_current_parameters()[column_name]

    return default_function


class Client(db.Model):  # type: ignore[name-defined]
    __tablename__ = "client"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    surname = db.Column(db.String(50), nullable=False)
    credit_card = db.Column(db.String(50))
    car_number = db.Column(db.String(10), unique=True)

    def __repr__(self):
        return f"клиент {self.name} {self.surname} (car number: {self.car_number})"

    def to_json(self) -> Dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class ParkingLot(db.Model):  # type: ignore[name-defined]
    __tablename__ = "parking_lot"

    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(100), nullable=False, unique=True)
    opened = db.Column(db.Boolean, default=False)
    count_places = db.Column(db.Integer, nullable=False)
    count_available_places = db.Column(
        db.Integer, nullable=False, default=same_as("count_places")
    )

    def __repr__(self):
        return f"паркинг по адресу: {self.address} (всего мест: {self.count_places})"

    def to_json(self) -> Dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class ClientParking(db.Model):  # type: ignore[name-defined]
    __tablename__ = "client_parking"
    __table_args__ = (
        UniqueConstraint("client_id", "parking_id", name="unique_client_parking"),
    )

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"))
    parking_id = db.Column(db.Integer, db.ForeignKey("parking_lot.id"))
    time_in = db.Column(db.DateTime, default=db.func.now())
    time_out = db.Column(db.DateTime, default=None)

    def __repr__(self):
        return f"клиент №{self.client_id} - паркинг №{self.parking_id}"

    def to_json(self) -> Dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

from typing import Any, List, Optional

from flask import Flask, Response, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///parking.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    # app.json.ensure_ascii = False
    db.init_app(app)

    from .models import Client, ClientParking, ParkingLot

    @app.before_request
    def before_request_func():
        # make the function work once after first request.
        app.before_request_funcs[None].remove(before_request_func)
        db.create_all()

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()

    @app.route("/clients", methods=["POST"])
    def create_client_handler():
        """Создание нового клиента"""
        name = request.form.get("name", type=str)
        surname = request.form.get("surname", type=str)
        credit_card = request.form.get("credit_card", type=str)
        car_number = request.form.get("car_number", type=str)

        new_client = Client(
            name=name, surname=surname, credit_card=credit_card, car_number=car_number
        )
        try:
            db.session.add(new_client)
            db.session.commit()
            return f"Новый {new_client.__repr__()} добавлен в базу", 201
        except IntegrityError as exc:
            return f"Ошибка: {exc.args[0]}", 500

    @app.route("/clients", methods=["GET"])
    def get_clients_handler():
        """Вывод всех клиентов"""
        clients: List[Client] = db.session.query(Client).all()
        if clients:
            clients_list = [client.to_json() for client in clients]
            return jsonify(clients_list), 200
        else:
            return Response(response="База пуста.", status=200), 200

    @app.route("/clients/<int:client_id>", methods=["GET"])
    def get_client_by_id_handler(client_id: int):
        """Вывод клиента по ID"""

        client: Optional[Any] = db.session.query(Client).get(client_id)
        if client:
            return jsonify(client.to_json()), 200
        else:
            return Response(response="Такой клиент не найден.", status=500), 500

    @app.route("/parkings", methods=["POST"])
    def create_parking_handler():
        """Создание нового паркинга"""
        address = request.form.get("address", type=str)
        opened = request.form.get("opened", type=bool)
        count_places = request.form.get("count_places", type=int)
        count_available_places = request.form.get("count_available_places", type=int)

        new_parking = ParkingLot(
            address=address,
            opened=opened,
            count_places=count_places,
            count_available_places=count_available_places,
        )
        try:
            db.session.add(new_parking)
            db.session.commit()
            return f"Новый {new_parking.__repr__()} добавлен в базу", 201
        except IntegrityError as exc:
            return f"Ошибка: {exc.args[0]}", 500

    @app.route("/client_parkings/<int:client_id>/<int:parking_id>", methods=["POST"])
    def create_parking_entry_handler(client_id: int, parking_id: int):
        """Регистрация заезда на паркинг"""

        client_data: Optional[Client] = db.session.get(Client, client_id)
        lot_data: Optional[ParkingLot] = db.session.get(ParkingLot, parking_id)

        if lot_data:
            if lot_data.opened:
                if lot_data.count_available_places >= 1:
                    if client_data:
                        try:
                            new_client_parking = ClientParking(
                                client_id=client_id,
                                parking_id=parking_id,
                            )

                            db.session.add(new_client_parking)

                            # available_place_decrement
                            db.session.query(ParkingLot).filter(
                                ParkingLot.id == parking_id
                            ).update(
                                {
                                    "count_available_places": ParkingLot.count_available_places
                                    - 1
                                }
                            )

                            db.session.commit()
                            return (
                                f"Регистрация успешна: {new_client_parking.__repr__()}",
                                201,
                            )
                        except IntegrityError as exc:
                            return f"Ошибка: {exc.args[0]}", 500
                    else:
                        return f"Ошибка: клиент №{client_id} не зарегистрирован.", 500
                else:
                    return (
                        f"Ошибка: свободных мест нет на паркинге №{parking_id} ",
                        500,
                    )
            else:
                return f"Ошибка: паркинг №{parking_id} закрыт.", 500
        else:
            return f"Ошибка: паркинг №{parking_id} не существует в базе.", 500

    @app.route("/client_parkings/<int:client_id>/<int:parking_id>", methods=["DELETE"])
    def create_parking_exit_handler(client_id: int, parking_id: int):
        """Регистрация выезда с паркинга"""

        client_data: Optional[Client] = db.session.get(Client, client_id)
        lot_data: Optional[ParkingLot] = db.session.get(ParkingLot, parking_id)

        if lot_data:
            if client_data:
                if client_data.credit_card:
                    try:
                        db.session.query(ClientParking).filter(
                            ClientParking.client_id == client_id
                        ).update({"time_out": db.func.now()})

                        # available_place_increment
                        db.session.query(ParkingLot).filter(
                            ParkingLot.id == parking_id
                        ).update(
                            {
                                "count_available_places": ParkingLot.count_available_places
                                + 1
                            }
                        )

                        db.session.commit()
                        return "Выезд разрешён.", 201

                    except IntegrityError as exc:
                        return f"Ошибка: {exc.args[0]}.", 500
                else:
                    return (
                        f"Ошибка: платёжные реквизиты клиента №{client_id} не "
                        f"зарегистрированы.",
                        500,
                    )
            else:
                return f"Ошибка: клиент №{client_id} не зарегистрирован.", 500
        else:
            return f"Ошибка: паркинг №{parking_id} не существует в базе.", 500

    return app

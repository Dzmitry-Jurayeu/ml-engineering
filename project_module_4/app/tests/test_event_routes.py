import pytest
from fastapi import status
from fastapi.testclient import TestClient
from api import app
from services.crud import user as UserService
from models.event import ModelEvent, BalanceReplenishmentEvent
from models.balance import Balance
from models.model import Model
from sqlmodel import Session, select
from fastapi.encoders import jsonable_encoder


def test_create_model_event_w_zero_balance(client_common: TestClient, session: Session):
    query = select(Balance).where(Balance.user_id == client_common.user_id)
    balance_before = session.exec(query).first()
    message = {"text": "Не токсичный текст"}
    response = client_common.post("/api/events/new_model_event", json=message)
    query = select(ModelEvent).where(ModelEvent.text == message.get("text"))
    record_in_db = session.exec(query).first()
    query = select(Balance).where(Balance.user_id == client_common.user_id)
    balance_after = session.exec(query).first()

    assert response.status_code == status.HTTP_200_OK
    assert record_in_db is not None
    assert record_in_db.creator_id == client_common.user_id
    assert record_in_db.amount == len(message.get("text").split())
    assert record_in_db.response is not None
    assert balance_before.balance_value == balance_after.balance_value


def test_balance_replenishment_negative(client_common: TestClient, session: Session):
    query = select(Balance).where(Balance.user_id == client_common.user_id)
    balance_before = session.exec(query).first().balance_value
    amount = {"amount": -100}
    response = client_common.post("/api/events/new_my_balance_event", json=amount)
    query = select(Balance).where(Balance.user_id == client_common.user_id)
    balance_after = session.exec(query).first().balance_value

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "The balance replenishment amount must be > 0"}
    assert balance_before == balance_after


def test_balance_replenishment_positive(client_common: TestClient, session: Session):
    query = select(Balance).where(Balance.user_id == client_common.user_id)
    balance_before = session.exec(query).first().balance_value
    amount = {"amount": 100}
    response = client_common.post("/api/events/new_my_balance_event", json=amount)
    query = select(Balance).where(Balance.user_id == client_common.user_id)
    balance_after = session.exec(query).first().balance_value

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "Balance event created successfully. Balance replenished."}
    assert balance_before + amount.get("amount") == balance_after


def test_create_model_event_w_correct_balance(client_common: TestClient, session: Session):
    query = select(Balance).where(Balance.user_id == client_common.user_id)
    balance_before = session.exec(query).first().balance_value
    message = {"text": "Текс со списанием баланса"}
    response = client_common.post("/api/events/new_model_event", json=message)
    query = select(ModelEvent).where(ModelEvent.text == message.get("text"))
    record_in_db = session.exec(query).first()
    query = select(Balance).where(Balance.user_id == client_common.user_id)
    balance_after = session.exec(query).first().balance_value

    assert response.status_code == status.HTTP_200_OK
    assert record_in_db is not None
    assert record_in_db.creator_id == client_common.user_id
    assert record_in_db.amount == len(message.get("text").split())
    assert record_in_db.response is not None
    assert balance_before - len(message.get("text").split()) == balance_after


def test_get_balance_replenishment_history(client_common: TestClient):
    response = client_common.get("/api/events/retrieve_all_balance_events")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1


def test_get_model_request_history(client_common: TestClient):
    response = client_common.get("/api/events/retrieve_all_model_events")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 2


def test_get_balance_event_by_id(client_admin: TestClient, session: Session):
    payload = {"balance_event_id": 1}
    response = client_admin.get("/api/events/balance_event/{balance_event_id}".format(**payload))
    query = select(BalanceReplenishmentEvent).where(
        BalanceReplenishmentEvent.event_id == payload.get("balance_event_id"))
    record_in_db = session.exec(query).first()
    record_in_db = jsonable_encoder(record_in_db)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == record_in_db


def test_get_balance_event_by_non_existent_id(client_admin: TestClient):
    payload = {"balance_event_id": 5}
    response = client_admin.get("/api/events/balance_event/{balance_event_id}".format(**payload))

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": f"Balance event with ID {payload.get("balance_event_id")} not found"}


def test_get_balance_event_by_id_common_user(client_common: TestClient):
    payload = {"balance_event_id": 1}
    response = client_common.get("/api/events/balance_event/{balance_event_id}".format(**payload))

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "Insufficient permissions"}


def test_get_model_event_by_id(client_admin: TestClient, session: Session):
    payload = {"model_event_id": 1}
    response = client_admin.get("/api/events/model_event/{model_event_id}".format(**payload))
    query = select(ModelEvent).where(ModelEvent.event_id == payload.get("model_event_id"))
    record_in_db = session.exec(query).first()
    record_in_db = jsonable_encoder(record_in_db)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == record_in_db


def test_get_model_event_by_non_existent_id(client_admin: TestClient):
    payload = {"model_event_id": 5}
    response = client_admin.get("/api/events/model_event/{model_event_id}".format(**payload))

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": f"Model event with ID {payload.get("model_event_id")} not found"}


def test_get_model_event_by_id_common_user(client_common: TestClient):
    payload = {"model_event_id": 1}
    response = client_common.get("/api/events/model_event/{model_event_id}".format(**payload))

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "Insufficient permissions"}


def test_balance_replenishment_by_id_admin_positive(client_admin: TestClient, session: Session):
    data = {"user_id": 2}
    payload = {"amount": 100}
    query = select(Balance).where(Balance.user_id == data.get("user_id"))
    balance_before = session.exec(query).first().balance_value
    response = client_admin.post("/api/events/new_balance_event", json=payload, params=data)
    query = select(Balance).where(Balance.user_id == data.get("user_id"))
    balance_after = session.exec(query).first().balance_value

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "Balance replenishment event created successfully. Balance replenished."}
    assert balance_before + payload.get("amount") == balance_after


def test_balance_replenishment_by_id_admin_negative(client_admin: TestClient, session: Session):
    data = {"user_id": 1}
    payload = {"amount": -100}
    query = select(Balance).where(Balance.user_id == data.get("user_id"))
    balance_before = session.exec(query).first().balance_value
    response = client_admin.post("/api/events/new_balance_event", json=payload, params=data)
    query = select(Balance).where(Balance.user_id == data.get("user_id"))
    balance_after = session.exec(query).first().balance_value

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "The balance replenishment amount must be > 0"}
    assert balance_before == balance_after


def test_balance_replenishment_by_id_common(client_common: TestClient):
    data = {"user_id": 1}
    amount = {"amount": 100}
    response = client_common.post("/api/events/new_balance_event", json=amount, params=data)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "Insufficient permissions"}


def test_send_task(client_common: TestClient, session: Session):
    message = {"text": "Текс с отправкой задачи"}
    response = client_common.post("/api/events/send_task", json=message)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "Task sent successfully!"}


def test_task_result(client_common: TestClient, session: Session):
    query = select(ModelEvent).where(ModelEvent.text == "Текс с отправкой задачи")
    record_in_db = session.exec(query).first()
    message = {
        'user_id': client_common.user_id,
        'event_id': record_in_db.event_id,
        'score': 0.0024932280648499727,
        'response': 'No',
        'amount': len("Текс с отправкой задачи".split())}
    response = client_common.post("/api/events/task_result", json=message)
    query = select(ModelEvent).where(ModelEvent.event_id == record_in_db.event_id)
    record_in_db = session.exec(query).first()

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"Result": "Data received and updated."}
    assert record_in_db.score == 0.0024932280648499727
    assert record_in_db.response == 'No'
    assert record_in_db.amount == len("Текс с отправкой задачи".split())

def test_delete_balance_event_by_non_existent_id(client_admin: TestClient):
    payload = {"balance_event_id": 5}
    response = client_admin.delete("/api/events/balance_event/{balance_event_id}".format(**payload))

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Balance event with supplied ID does not exist"}


def test_delete_balance_event_by_id_common_user(client_common: TestClient):
    payload = {"balance_event_id": 1}
    response = client_common.delete("/api/events/balance_event/{balance_event_id}".format(**payload))

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "Insufficient permissions"}


def test_delete_balance_event_by_id(client_admin: TestClient, session: Session):
    payload = {"balance_event_id": 1}
    response = client_admin.delete("/api/events/balance_event/{balance_event_id}".format(**payload))
    print(response.json())
    query = select(BalanceReplenishmentEvent).where(
        BalanceReplenishmentEvent.event_id == payload.get("balance_event_id"))
    record_in_db = session.exec(query).first()

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "Balance event deleted successfully"}
    assert record_in_db is None


def test_delete_model_event_by_non_existent_id(client_admin: TestClient):
    payload = {"model_event_id": 5}
    response = client_admin.delete("/api/events/model_event/{model_event_id}".format(**payload))

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Model event with supplied ID does not exist"}


def test_delete_model_event_by_id_common_user(client_common: TestClient):
    payload = {"model_event_id": 1}
    response = client_common.delete("/api/events/model_event/{model_event_id}".format(**payload))

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "Insufficient permissions"}


def test_delete_model_event_by_id(client_admin: TestClient, session: Session):
    payload = {"model_event_id": 1}
    response = client_admin.delete("/api/events/model_event/{model_event_id}".format(**payload))
    query = select(ModelEvent).where(ModelEvent.event_id == payload.get("model_event_id"))
    record_in_db = session.exec(query).first()

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "Model event deleted successfully"}
    assert record_in_db is None


def test_delete_all_events_common_user(client_common: TestClient):
    response = client_common.delete("/api/events")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "Insufficient permissions"}


def test_delete_all_events(client_admin: TestClient, session: Session):
    response = client_admin.delete("/api/events")
    query = select(ModelEvent)
    model_events_db = session.exec(query).all()
    query = select(BalanceReplenishmentEvent)
    balance_events_db = session.exec(query).all()

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "Events deleted successfully"}
    assert len(model_events_db) == 0
    assert len(balance_events_db) == 0

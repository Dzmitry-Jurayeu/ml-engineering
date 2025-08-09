import jwt
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from fastapi.encoders import jsonable_encoder
from api import app
from services.crud import user as UserService
from models.event import ModelEvent, BalanceReplenishmentEvent
from models.balance import Balance
from models.model import Model
from routes.user import user_route, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token
from sqlmodel import Session, select


def test_get_all_balances_common(client_common: TestClient):
    response = client_common.get("/api/balances")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "Insufficient permissions"}


def test_get_all_balances_admin(client_admin: TestClient, session: Session):
    response = client_admin.get("/api/balances")
    query = select(Balance)
    record_in_db = session.exec(query).all()

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == len(record_in_db)


def test_get_my_balance(client_common: TestClient, session: Session):
    response = client_common.get("/api/balances/me")
    query = select(Balance).where(Balance.user_id == client_common.user_id)
    record_in_db = session.exec(query).first()
    record_in_db = jsonable_encoder(record_in_db)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == record_in_db


def test_get_balance_by_id(client_admin: TestClient, session: Session):
    payload = {"balance_id": 1}
    response = client_admin.get("/api/balances/balance_id/{balance_id}".format(**payload))
    query = select(Balance).where(Balance.balance_id == payload.get("balance_id"))
    record_in_db = session.exec(query).first()
    record_in_db = jsonable_encoder(record_in_db)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == record_in_db


def test_get_balance_by_non_existent_id(client_admin: TestClient):
    payload = {"balance_id": 5}
    response = client_admin.get("/api/balances/balance_id/{balance_id}".format(**payload))

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": f"Balance with ID {payload.get("balance_id")} not found"}


def test_get_balance_by_id_common_user(client_common: TestClient):
    payload = {"balance_id": 1}
    response = client_common.get("/api/balances/balance_id/{balance_id}".format(**payload))

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "Insufficient permissions"}


def test_clear_db(drop_session: Session):
    user_db = drop_session.exec(select(ModelEvent)).first()
    model_event_db = drop_session.exec(select(ModelEvent)).first()
    model_db = drop_session.exec(select(Model)).first()
    balance_db = drop_session.exec(select(Balance)).first()
    balance_replenishment_event_db = drop_session.exec(select(BalanceReplenishmentEvent)).first()

    assert user_db is None
    assert model_event_db is None
    assert model_db is None
    assert balance_db is None
    assert balance_replenishment_event_db is None

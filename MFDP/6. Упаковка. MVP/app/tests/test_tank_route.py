import jwt
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from api import app
from services.crud import tank as UserService


def test_get_tank_by_id(client_common: TestClient):
    payload = {"tank_id": 1}
    response = client_common.get("/api/tanks/tanks/{tank_id}".format(**payload))

    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("tank_id") == payload.get("tank_id")


def test_get_all_tanks(client_common: TestClient):
    response = client_common.get("/api/tanks/retrieve_all_tanks")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() is not None
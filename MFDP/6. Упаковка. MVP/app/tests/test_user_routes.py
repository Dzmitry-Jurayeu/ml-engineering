import jwt
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from api import app
from services.crud import user as UserService
from models.user import User
from sqlmodel import Session

def test_signin_admin_success(client: TestClient):
    response = client.get("/api/users/signin", follow_redirects=False)

    assert response.status_code == status.HTTP_302_FOUND


def test_signin_common_success(client: TestClient):
    response = client.get("/api/users/signin", follow_redirects=False)

    assert response.status_code == status.HTTP_302_FOUND

def test_get_me(client_common: TestClient, session: Session):
    user = User(
        user_id=88444060,
        is_admin=False
    )
    _ = UserService.create_user(user, session)

    response = client_common.get("/api/users/me")

    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("user_id") == client_common.user_id


def test_get_user_history(client_common: TestClient, session: Session):

    response = client_common.get("/api/users/get_user_history")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 0


def test_sign_out(client_common: TestClient, session: Session):
    response = client_common.post("/api/users/signout")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "Signed out successfully"}

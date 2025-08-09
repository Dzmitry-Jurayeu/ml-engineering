import jwt
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from api import app
from services.crud import user as UserService
from models.user import User
from routes.user import user_route, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token
from sqlmodel import Session, select


def test_signup_admin_success(client: TestClient, session: Session):
    user = {
        "email": "test_email_admin@gmail.com",
        "password": "my_secret_password",
        "is_admin": True
    }
    response = client.post("/api/users/signup", json=user)
    query = select(User).where(User.email == user.get("email"))
    user_in_db = session.exec(query).first()

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {"message": "User successfully registered"}
    assert user_in_db is not None
    assert user_in_db.email == user.get("email")
    assert user_in_db.is_admin == user.get("is_admin")


def test_signup_common_success(client: TestClient, session: Session):
    user = {
        "email": "test_email_common@gmail.com",
        "password": "my_secret_password",
    }
    response = client.post("/api/users/signup", json=user)
    query = select(User).where(User.email == user.get("email"))
    user_in_db = session.exec(query).first()

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {"message": "User successfully registered"}
    assert user_in_db is not None
    assert user_in_db.email == user.get("email")
    assert user_in_db.is_admin == False


def test_signup_email_wo_username(client: TestClient, session: Session):
    user = {
        "email": "@gmail.com",
        "password": "some_password",
    }
    response = client.post("/api/users/signup", json=user)
    query = select(User).where(User.email == user.get("email"))
    user_in_db = session.exec(query).first()

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": "Error creating user"}
    assert user_in_db is None


def test_signup_email_wo_at(client: TestClient, session: Session):
    user = {
        "email": "incorrect_emailgmail.com",
        "password": "some_password",
    }
    response = client.post("/api/users/signup", json=user)
    query = select(User).where(User.email == user.get("email"))
    user_in_db = session.exec(query).first()

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": "Error creating user"}
    assert user_in_db is None


def test_signup_email_wo_mail_server(client: TestClient, session: Session):
    user = {
        "email": "incorrect_email@.com",
        "password": "some_password",
    }
    response = client.post("/api/users/signup", json=user)
    query = select(User).where(User.email == user.get("email"))
    user_in_db = session.exec(query).first()

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": "Error creating user"}
    assert user_in_db is None


def test_signup_email_wo_domain(client: TestClient, session: Session):
    user = {
        "email": "incorrect_email@gmail.",
        "password": "some_password",
    }
    response = client.post("/api/users/signup", json=user)
    query = select(User).where(User.email == user.get("email"))
    user_in_db = session.exec(query).first()

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": "Error creating user"}
    assert user_in_db is None


def test_signup_email_wo_dot(client: TestClient, session: Session):
    user = {
        "email": "incorrect_email@gmailcom",
        "password": "some_password",
    }
    response = client.post("/api/users/signup", json=user)
    query = select(User).where(User.email == user.get("email"))
    user_in_db = session.exec(query).first()

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": "Error creating user"}
    assert user_in_db is None


def test_signin_admin_success(client: TestClient):
    user = {
        "username": "test_email_admin@gmail.com",
        "password": "my_secret_password",
    }
    response = client.post("/api/users/signin", data=user)
    payload = jwt.decode(response.json().get("access_token"), SECRET_KEY, algorithms=[ALGORITHM])
    email = payload.get("sub")

    assert response.status_code == status.HTTP_200_OK
    assert email == user.get("username")


def test_signin_common_success(client: TestClient):
    user = {
        "username": "test_email_common@gmail.com",
        "password": "my_secret_password",
    }
    response = client.post("/api/users/signin", data=user)
    payload = jwt.decode(response.json().get("access_token"), SECRET_KEY, algorithms=[ALGORITHM])
    email = payload.get("sub")

    assert response.status_code == status.HTTP_200_OK
    assert email == user.get("username")


def test_signin_incorrect_email(client: TestClient):
    user = {
        "username": "incorrect_email@gmail.com",
        "password": "some_password",
    }
    response = client.post("/api/users/signin", data=user)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "User does not exist"}


def test_signin_incorrect_password(client: TestClient):
    user = {
        "username": "test_email_common@gmail.com",
        "password": "incorrect_password",
    }
    response = client.post("/api/users/signin", data=user)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "Wrong credentials passed"}


def test_get_me(client_common: TestClient):
    response = client_common.get("/api/users/me")

    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("user_id") == client_common.user_id


def test_get_user_history(client_common: TestClient):
    response = client_common.get("/api/users/get_user_history")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 0

def test_sign_out(client_common: TestClient):
    response = client_common.post("/api/users/signout")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "Signed out successfully"}

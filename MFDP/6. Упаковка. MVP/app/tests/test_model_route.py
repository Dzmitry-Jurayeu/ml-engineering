import pytest
from fastapi import status
from fastapi.testclient import TestClient
from api import app
from models.model import Model
from sqlmodel import Session, select


def test_get_all_models_empty(client_common: TestClient):
    response = client_common.get("/api/models")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 0


def test_add_model(client_common: TestClient, session: Session):
    message = {
        "version": 1,
        "path": "./ml/AutogluonModels/ag-20251205_150250"
    }
    response = client_common.post("/api/models/new_model", json=message)
    query = select(Model).where(Model.version == message.get("version"),
                                Model.path == message.get("path"))
    record_in_db = session.exec(query).first()

    assert response.status_code == status.HTTP_200_OK
    assert record_in_db is not None

def test_add_existing_model(client_common: TestClient, session: Session):
    message = {
        "version": 1,
        "path": "./ml/AutogluonModels/ag-20251205_150250"
    }
    response = client_common.post("/api/models/new_model", json=message)

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {"detail": "Model with this params already exists"}


def test_get_all_models(client_common: TestClient):
    response = client_common.get("/api/models")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1


def test_get_model_by_id(client_common: TestClient):
    payload = {"model_id": 1}
    answer = {
        "model_id": 1,
        "version": 1,
        "path": "./ml/AutogluonModels/ag-20251205_150250"
    }
    response = client_common.get("/api/models/id/{model_id}".format(**payload))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == answer


def test_get_model_by_non_existent_id(client_common: TestClient):
    payload = {"model_id": 2}
    answer = f"Model with ID {payload.get("model_id")} not found"
    response = client_common.get("/api/models/id/{model_id}".format(**payload))

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": answer}


def test_get_model_by_params(client_common: TestClient):

    payload = {"version": 1, "path": "./ml/AutogluonModels/ag-20251205_150250"}
    response = client_common.get("/api/models/params", params=payload)

    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("model_id") == 1


def test_get_model_by_non_existent_params(client_common: TestClient):

    payload = {"version": 2, "path": "./autogluon_model.joblib"}
    version = payload.get("version")
    path = payload.get("path")
    answer = f"Model with params:\n\tversion = {version}\n\tpath = {path},\nnot found"
    response = client_common.get("/api/models/params", params=payload)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": answer}

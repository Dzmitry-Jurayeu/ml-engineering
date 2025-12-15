import pytest
from fastapi import status
from fastapi.testclient import TestClient
from api import app
from services.crud import user as UserService
from models.event import Prediction, PredictionCandidate
from models.model import Model
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from services.crud.tank import init_tanks


def test_create_model_event(client_common: TestClient, session: Session):
    general_df, premium_df = init_tanks(session)
    client_common.app.state.general_df = general_df
    client_common.app.state.premium_df = premium_df

    response = client_common.get("/api/events/new_model_event")
    query = select(Prediction).where(Prediction.creator_id == client_common.user_id)
    record_in_db = session.exec(query).first()

    assert response.status_code == status.HTTP_200_OK
    assert record_in_db is not None


def test_get_model_event_by_id(client_admin: TestClient, session: Session):
    payload = {"model_event_id": 1}
    response = client_admin.get("/api/events/model_event/{model_event_id}".format(**payload))
    stmt = select(Prediction).where(Prediction.prediction_id == payload.get("model_event_id"))
    stmt = stmt.options(
        selectinload(Prediction.candidates).selectinload(PredictionCandidate.tank)
    ).order_by(Prediction.timestamp)

    results = session.exec(stmt).one_or_none()
    if results:
        out = {
            "prediction_id": results.prediction_id,
            "creator_id": results.creator_id,
            "timestamp": results.timestamp.isoformat(),
            "candidates": [
                {
                    "rank": c.rank,
                    "tank_id": c.tank_id,
                    "predicted_damage": c.predicted_damage,
                    "tank_name": c.tank.name if c.tank else None,
                    "tank_tier": c.tank.tier if c.tank else None,
                    "tank_nation": c.tank.nation if c.tank else None,
                    "tank_type": c.tank.type if c.tank else None,
                    "tank_image": c.tank.image if c.tank else None,
                }
                for c in sorted(results.candidates, key=lambda x: x.rank)
            ]
        }

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == out


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


def test_send_task(client_common: TestClient, session: Session):
    response = client_common.get("/api/events/send_task")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "Task sent successfully!"}


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
    query = select(Prediction).where(Prediction.prediction_id == payload.get("model_event_id"))
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
    query = select(Prediction)
    model_events_db = session.exec(query).all()

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "Events deleted successfully"}
    assert len(model_events_db) == 0

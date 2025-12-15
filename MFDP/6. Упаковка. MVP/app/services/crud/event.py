from typing import List, Optional
from models.model import Model
from models.event import Prediction, PredictionCandidate
from ml.prediction import predict
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from loguru import logger


def get_all_model_events(user, session) -> List[Prediction]:
    stmt = select(Prediction)
    if not user.is_admin:
        stmt = stmt.where(Prediction.creator_id == user.user_id)

    stmt = stmt.options(
        selectinload(Prediction.candidates).selectinload(PredictionCandidate.tank)
    ).order_by(Prediction.timestamp)

    results = session.exec(stmt).scalars().all()

    out = []
    for el in results:
        out.append({
            "prediction_id": el.prediction_id,
            "creator_id": el.creator_id,
            "timestamp": el.timestamp,
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
                for c in sorted(el.candidates, key=lambda x: x.rank)
            ]
        })
    return out


def get_model_event_by_id(id: int, session) -> Optional[Prediction]:
    stmt = select(Prediction).where(Prediction.prediction_id == id)
    stmt = stmt.options(
        selectinload(Prediction.candidates).selectinload(PredictionCandidate.tank)
    ).order_by(Prediction.timestamp)

    results = session.exec(stmt).scalars().one_or_none()
    if results:
        out = {
                "prediction_id": results.prediction_id,
                "creator_id": results.creator_id,
                "timestamp": results.timestamp,
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
        return out
    return None


def update_model_event(event: Prediction, session, model, general_df, premium_df) -> Prediction:
    res = predict(model, event.creator_id, general_df, premium_df)
    for enum, el in enumerate(res.itertuples()):
        event_candidates = PredictionCandidate()
        event_data = {
            "prediction_id": event.prediction_id,
            "rank": enum + 1,
            "tank_id": el.tank_id,
            "predicted_damage": el.preds
        }
        for key, value in event_data.items():
            setattr(event_candidates, key, value)

        session.add(event_candidates)
        session.commit()
        session.refresh(event_candidates)
    return get_model_event_by_id(event.prediction_id, session)


def update_task_model_event(data: dict, session):
    for el in data.get("result"):
        event_candidates = PredictionCandidate()
        for key, value in el.items():
            setattr(event_candidates, key, value)

        session.add(event_candidates)
        session.commit()
        session.refresh(event_candidates)

    return None


def create_model_event(new_event: Prediction, session) -> None:
    session.add(new_event)
    session.commit()
    session.refresh(new_event)
    return new_event


def delete_all_events(session) -> None:
    session.query(Prediction).delete()
    session.commit()


def delete_model_events_by_id(id: int, session) -> None:
    event = session.get(Prediction, id)
    if event:
        session.delete(event)
        session.commit()
        return None

    raise Exception("Event with supplied ID does not exist")

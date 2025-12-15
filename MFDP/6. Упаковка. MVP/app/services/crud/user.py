from models.user import User
from models.event import Prediction, PredictionCandidate
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload


def get_all_users(session) -> List[User]:
    return session.query(User).all()


def get_user_by_id(user_id: int, session) -> Optional[User]:
    users = session.get(User, user_id)
    if users:
        return users
    return None


def create_user(new_user: User, session) -> None:
    users = session.get(User, new_user.user_id)
    if not users:
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
    return new_user


def get_user_history(requestor: User, session):
    stmt = select(Prediction)
    if not requestor.is_admin:
        stmt = stmt.where(Prediction.creator_id == requestor.user_id)

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


def grant_admin_status(id: int, session):
    user = session.query(User).filter(User.user_id == id).first()
    if user.is_admin:
        return {"message": f"The user with ID {id} is admin already."}
    else:
        user.is_admin = True
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"message": f"Admin status is provided to the user with ID {id}."}


def revoke_admin_status(id: int, session):
    user = session.query(User).filter(User.user_id == id).first()
    if not user.is_admin:
        return {"message": f"The user with ID {id} doesn't have admin status."}
    else:
        user.is_admin = False
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"message": f"Admin status is revoked for the user with ID {id}."}

from models.tank import Tank
from helper.helper import get_tanks_data
from typing import List, Optional

def get_all_tanks(session) -> List[Tank]:
    return session.query(Tank).all()


def get_tank_by_id(id: int, session) -> Optional[Tank]:
    tanks = session.get(Tank, id)
    if tanks:
        return tanks
    return None

def init_tanks(session):
    general_df, premium_df, db_tanks_df = get_tanks_data()
    for el in db_tanks_df.to_dict(orient="records"):
        tank = Tank()
        for key, value in el.items():
            setattr(tank, key, value)

        session.add(tank)
        session.commit()
        session.refresh(tank)
    return general_df, premium_df
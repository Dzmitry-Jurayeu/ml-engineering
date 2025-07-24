from models.event import Event, ModelEvent
from models.balance import Balance
from typing import List, Optional
from models.model import Model
from services.crud.balance import balance_withdraw


def get_all_events(session) -> List[Event]:
    return session.query(Event).all()


def get_event_by_id(id: int, session) -> Optional[Event]:
    event = session.get(Event, id)
    if event:
        return event
    return None


def update_model_event(event: ModelEvent, session, model) -> Event:
    balance = session.get(Balance, event.creator_id)
    cost = len(event.text.split())
    if balance.balance_value < cost:
        event_data = {
            "response": "Insufficient funds.",
            "amount": cost
        }
    else:
        score = model(event.text)[0].get("score")
        event_data = {
            "score": score,
            "response": "Yes" if score > 0.5 else "No",
            "amount": cost
        }
        balance_withdraw(event, session)
    for key, value in event_data.items():
        setattr(event, key, value)

    session.add(event)
    session.commit()
    session.refresh(event)
    return event


def create_event(new_event: Event, session) -> None:
    session.add(new_event)
    session.commit()
    session.refresh(new_event)


def delete_all_events(session) -> None:
    session.query(Event).delete()
    session.commit()


def delete_events_by_id(id: int, session) -> None:
    event = session.get(Event, id)
    if event:
        session.delete(event)
        session.commit()
        return

    raise Exception("Event with supplied ID does not exist")
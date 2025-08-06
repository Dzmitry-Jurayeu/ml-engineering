from models.balance import Balance
from typing import List, Optional, Union
from models.model import Model
from models.event import ModelEvent, BalanceReplenishmentEvent
from services.crud.balance import balance_withdraw


def get_all_events(user, session) -> List[Union[ModelEvent, BalanceReplenishmentEvent]]:
    if user.is_admin:
        model_events = session.query(ModelEvent).all()
        balance_events = session.query(BalanceReplenishmentEvent).all()
    else:
        model_events = session.query(ModelEvent).filter(ModelEvent.creator_id == user.user_id).all()
        balance_events = session.query(BalanceReplenishmentEvent).filter(
            BalanceReplenishmentEvent.creator_id == user.user_id).all()
    sorted_user_history = sorted(model_events + balance_events, key=lambda x: x.timestamp)
    return sorted_user_history


def get_all_balance_events(user, session) -> List[BalanceReplenishmentEvent]:
    if user.is_admin:
        balance_events = session.query(BalanceReplenishmentEvent).all()
    else:
        balance_events = session.query(BalanceReplenishmentEvent).filter(
            BalanceReplenishmentEvent.creator_id == user.user_id).all()
    return balance_events


def get_all_model_events(user, session) -> List[ModelEvent]:
    if user.is_admin:
        model_events = session.query(ModelEvent).all()
    else:
        model_events = session.query(ModelEvent).filter(ModelEvent.creator_id == user.user_id).all()
    return model_events


def get_balance_event_by_id(id: int, session) -> Optional[BalanceReplenishmentEvent]:
    event = session.get(BalanceReplenishmentEvent, id)
    if event:
        return event
    return None


def get_model_event_by_id(id: int, session) -> Optional[ModelEvent]:
    event = session.get(ModelEvent, id)
    if event:
        return event
    return None


def update_model_event(event: ModelEvent, session, model) -> ModelEvent:
    balance = session.get(Balance, event.creator_id)
    cost = len(event.text.split())
    if balance.balance_value < cost:
        event_data = {
            "response": f"Insufficient funds. You need {cost} credits.",
            "amount": cost
        }
    else:
        score = model(event.text)[0].get("score")
        event_data = {
            "score": score,
            "response": "Yes" if score > 0.5 else "No",
            "amount": cost
        }
    for key, value in event_data.items():
        setattr(event, key, value)

    if balance.balance_value >= cost:
        balance_withdraw(event, session)

    session.add(event)
    session.commit()
    session.refresh(event)
    return event

def update_task_model_event(data: dict, session) -> ModelEvent:
    balance = session.get(Balance, data.get("user_id"))
    event = get_model_event_by_id(data.get("event_id"), session)
    event_data = {k: v for k, v in data.items() if k in ["score", "response", "amount"]}

    for key, value in event_data.items():
        setattr(event, key, value)

    if balance.balance_value >= event.amount:
        balance_withdraw(event, session)

    session.add(event)
    session.commit()
    session.refresh(event)
    return event


def create_model_event(new_event: ModelEvent, session) -> None:
    session.add(new_event)
    session.commit()
    session.refresh(new_event)
    return new_event


def create_balance_event(new_event: BalanceReplenishmentEvent, session) -> None:
    session.add(new_event)
    session.commit()
    session.refresh(new_event)
    return new_event


def delete_all_events(session) -> None:
    session.query(ModelEvent).delete()
    session.query(BalanceReplenishmentEvent).delete()
    session.commit()


def delete_model_events_by_id(id: int, session) -> None:
    event = session.get(ModelEvent, id)
    if event:
        session.delete(event)
        session.commit()
        return

    raise Exception("Event with supplied ID does not exist")


def delete_balance_events_by_id(id: int, session) -> None:
    event = session.get(BalanceReplenishmentEvent, id)
    if event:
        session.delete(event)
        session.commit()
        return

    raise Exception("Event with supplied ID does not exist")

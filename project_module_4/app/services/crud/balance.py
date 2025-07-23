from models.balance import Balance
from typing import List, Optional
from models.event import ModelEvent, BalanceReplenishmentEvent

def get_all_balances(session) -> List[Balance]:
    return session.query(Balance).all()

def get_balance_by_id(id:int, session) -> Optional[Balance]:
    balances = session.get(Balance, id)
    if balances:
        return balances
    return None

def balance_replenishment(event: BalanceReplenishmentEvent, session) -> Balance:
    balance = session.get(Balance, event.creator_id)
    if balance:
        event_data = {
            "balance_value": event.amount,
            "last_update": event.timestamp
        }
    for key, value in event_data.items():
        setattr(balance, key, value)

    session.add(balance)
    session.commit()
    session.refresh(balance)
    return balance

def balance_withdraw(event: ModelEvent, session) -> Balance:
    balance = session.get(Balance, event.creator_id)
    if balance:
        event_data = {
            "balance_value": balance.balance_value - event.amount,
            "last_update": event.timestamp
        }
    for key, value in event_data.items():
        setattr(balance, key, value)

    session.add(balance)
    session.commit()
    session.refresh(balance)
    return balance
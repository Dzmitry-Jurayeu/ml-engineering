from models.user import User
from models.balance import Balance
from models.event import ModelEvent, BalanceReplenishmentEvent
from typing import List, Optional
import bcrypt
import re

def get_all_users(session) -> List[User]:
    return session.query(User).all()

def get_user_by_id(id:int, session) -> Optional[User]:
    users = session.get(User, id)
    if users:
        return users
    return None

def get_user_by_email(email:str, session) -> Optional[User]:
    user = session.query(User).filter(User.email == email).first()
    if user:
        return user
    return None

def create_user(new_user: User, session) -> None:
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    if not email_pattern.match(new_user.email):
        raise ValueError("Invalid email format")

    new_user.balance = Balance()
    salt = bcrypt.gensalt()
    new_user.password = bcrypt.hashpw(new_user.password.encode("utf-8"), salt).decode('utf-8')
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

def get_user_history(requestor: User, user: User, session):
    if requestor.is_admin:
        model_events = session.query(ModelEvent).all()
        balance_events = session.query(BalanceReplenishmentEvent).all()
    else:
        model_events = session.query(User).filter(User.user_id == user.user_id).all()
        balance_events = session.query(User).filter(User.user_id == user.user_id).all()
    return model_events, balance_events

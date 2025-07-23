from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from models.event import BalanceReplenishmentEvent, ModelEvent
    from models.user import User


class Balance(SQLModel, table=True):
    """
    Класс для представления баланса пользователя.

    Attributes:
        balance_id (int): Уникальный идентификатор баланса
        last_update (datetime): Дата и время последнего изменения баланса
        balance_value (int): Баланс пользователя
    """
    balance_id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.user_id")
    user: 'User' = Relationship(
        back_populates="balance",
        sa_relationship_kwargs={"lazy": "selectin"}
    )
    last_update: datetime = Field(default_factory=datetime.utcnow)
    balance_value: int = Field(default=0)

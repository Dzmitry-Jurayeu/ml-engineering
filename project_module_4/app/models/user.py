from typing import List, TYPE_CHECKING, Union, Optional
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from models.balance import Balance
    from models.event import ModelEvent, BalanceReplenishmentEvent


class User(SQLModel, table=True):
    """
    Класс для представления пользователя в системе.

    Attributes:
        user_id (int): Уникальный идентификатор пользователя
        email (str): Email пользователя
        password (str): Пароль пользователя
        balance ('Balance'): Идентификатор баланса пользователя
        model_events (List[ModelEvent]): Список событий обращения к модели
        balance_events (List[BalanceReplenishmentEvent]): Список событий с балансом
    """
    user_id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(
        nullable=False,
        unique=True,
        index=True,
        min_length=5,
        max_length=255
    )
    password: str = Field(
        nullable=False,
        index=True,
        min_length=8
    )
    balance: 'Balance' = Relationship(
        back_populates="user",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "lazy": "selectin"
        }
    )
    model_events: List['ModelEvent'] = Relationship(
        back_populates="creator",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "lazy": "selectin"
        }
    )
    balance_events: List['BalanceReplenishmentEvent'] = Relationship(
        back_populates="creator",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "lazy": "selectin"
        }
    )
    is_admin: bool = Field(
        default=False,
        nullable=False,
    )

    class Config:
        validate_assignment = True
        arbitrary_types_allowed = True
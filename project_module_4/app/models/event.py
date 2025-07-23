from datetime import datetime
from models.model import Model
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship


if TYPE_CHECKING:
    from models.user import User


class Event(SQLModel):
    """
    Базовый класс для представления события.

    Attributes:
        event_id (int): Уникальный идентификатор события
    """
    event_id: Optional[int] = Field(default=None, primary_key=True)


class ModelEvent(Event, table=True):
    """
    Класс для представления события запроса к модели.

    Attributes:
        event_id (int): Уникальный идентификатор события
        creator (User): Создатель события
        text (str): Путь к изображению события
        title (str): Название события
        score (float): Вероятность, предсказанная моделью
        response (str): Результат предсказания модели
        amount (int): Стоимость события
    """

    event_id: Optional[int] = Field(
        default=None,
        primary_key=True,
    )
    creator_id: Optional[int] = Field(default=None, foreign_key="user.user_id")

    creator: Optional['User'] = Relationship(
        back_populates="model_events",
        sa_relationship_kwargs={"lazy": "selectin"}
    )
    text: Optional[str] = Field(default=None, min_length=1, max_length=300)
    title: str = Field(default="Model request", min_length=1, max_length=30)
    score: Optional[float] = Field(default=None)
    response: Optional[str] = Field(default=None)
    amount: int = Field(default=0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class BalanceReplenishmentEvent(Event, table=True):
    """
    Класс для представления события пополнения баланса.

    Attributes:
        event_id (int): Уникальный идентификатор события
        creator (User): Создатель события
        title (str): Название события
        amount (int): Сумма пополнения баланса
    """

    event_id: Optional[int] = Field(
        default=None,
        primary_key=True,
    )
    creator_id: Optional[int] = Field(default=None, foreign_key="user.user_id")

    creator: Optional['User'] = Relationship(
        back_populates="balance_events",
        sa_relationship_kwargs={"lazy": "selectin"}
    )
    title: str = Field(default="Balance operation", min_length=1, max_length=30)
    amount: int = Field(default=0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

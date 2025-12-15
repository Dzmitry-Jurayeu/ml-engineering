from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Integer, ForeignKey as SA_ForeignKey

if TYPE_CHECKING:
    from models.tank import Tank
    from models.user import User


class Prediction(SQLModel, table=True):
    """
    Класс для представления события.

    Attributes:
        prediction_id (int): Уникальный идентификатор события
        creator_id (int): Уникальный ID игрока
        timestamp (datetime): Дата и время запроса
    """
    prediction_id: Optional[int] = Field(default=None, primary_key=True)
    creator_id: Optional[int] = Field(default=None, foreign_key="user.user_id")
    timestamp: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    creator: Optional["User"] = Relationship(back_populates="model_events")
    candidates: List["PredictionCandidate"] = Relationship(back_populates="prediction", sa_relationship_kwargs={
        "cascade": "all, delete-orphan",
        "lazy": "selectin",
        "order_by": "PredictionCandidate.rank",
        "passive_deletes": True
    })


class PredictionCandidate(SQLModel, table=True):
    """
    Класс для представления ранжирования.

    Attributes:
        uid (int): Уникальный идентификатор события
        prediction_id (int): Уникальный ID предсказания
        rank (datetime): Дата и время запроса
        tank_id (int): Уникальный ID танка
        predicted_damage (int): Предсказанное значение
        tank:
    """
    uid: Optional[int] = Field(default=None, primary_key=True)
    prediction_id: Optional[int] = Field(
        default=None,
        sa_column=Column(
            Integer,
            SA_ForeignKey("prediction.prediction_id", ondelete="CASCADE"),
            index=True,
            nullable=False
        )
    )
    rank: Optional[int] = Field(default=None)
    tank_id: Optional[int] = Field(foreign_key="tank.tank_id", index=True)
    predicted_damage: Optional[int] = Field(default=None)
    prediction: Optional[Prediction] = Relationship(back_populates="candidates")
    tank: Optional['Tank'] = Relationship(back_populates="candidates", sa_relationship_kwargs={"lazy": "selectin"})

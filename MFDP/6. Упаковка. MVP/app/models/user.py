from typing import List, TYPE_CHECKING, Optional
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from models.event import Prediction


class User(SQLModel, table=True):
    """
    Класс для представления пользователя в системе.

    Attributes:
        user_id (int): Уникальный ID игрока
        model_events (List[ModelEvent]): Список событий обращения к модели
        is_admin (bool): Является ли пользователь Администратором
    """
    user_id: Optional[int] = Field(default=None, primary_key=True)
    model_events: List['Prediction'] = Relationship(
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
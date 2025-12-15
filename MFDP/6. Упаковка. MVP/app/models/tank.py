from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING, List

if TYPE_CHECKING:
    from models.event import PredictionCandidate


class Tank(SQLModel, table=True):
    """
    Класс для представления танков.

    Attributes:
        tank_id (int): Уникальный идентификатор танка
        name (str): Название танка
        tier (int): Уровень танка
        nation (str): Нация танка
        type (str): Тип танка
        is_premium (bool): Является ли танк премиумным
        image (str): Ссылка на изображение танка
    """
    tank_id: Optional[int] = Field(default=None, primary_key=True)
    name: Optional[str] = Field(default=None)
    tier: Optional[int] = Field(default=None)
    nation: Optional[str] = Field(default=None)
    type: Optional[str] = Field(default=None)
    is_premium: Optional[bool] = Field(default=None)
    image: Optional[str] = Field(default=None)
    candidates: List['PredictionCandidate'] = Relationship(back_populates="tank",
                                                           sa_relationship_kwargs={"lazy": "selectin"})

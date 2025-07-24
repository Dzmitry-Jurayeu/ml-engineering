from typing import Optional
from sqlmodel import SQLModel, Field


class Model(SQLModel, table=True):
    """
    Класс для представления модели.

    Attributes:
        task (str): Название модели
        model_name (str): Наименование модели
    """
    model_id: Optional[int] = Field(default=None, primary_key=True)
    task: Optional[str] = Field(default="text-classification")
    model_name: Optional[str] = Field(default="unitary/toxic-bert")

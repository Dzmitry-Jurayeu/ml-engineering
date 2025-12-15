from typing import Optional
from sqlmodel import SQLModel, Field


class Model(SQLModel, table=True):
    """
    Класс для представления модели.

    Attributes:
        model_id (int): ID модели
        version (int): Версия модели
        path (str): Путь к модели
    """
    model_id: Optional[int] = Field(default=None, primary_key=True)
    version: Optional[int] = Field(default=1)
    path: Optional[str] = Field(default="./ml/AutogluonModels/ag-20251205_150250")
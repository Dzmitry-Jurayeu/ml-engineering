from dataclasses import dataclass
from transformers import pipeline


@dataclass
class Model:
    """
    Класс для представления модели.

    Attributes:
        task (str): Название модели
        model_name (str): Наименование модели
    """
    task: str = "text-classification"
    model_name: str = "unitary/toxic-bert"

    def __post_init__(self) -> None:
        self.model = pipeline(self.task, model=self.model_name)

    def predict(self, text) -> list:
        return self.model(text)

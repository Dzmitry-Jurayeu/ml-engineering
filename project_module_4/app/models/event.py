from dataclasses import dataclass
from datetime import datetime
from models.user import User
from models.model import Model


@dataclass
class Event:
    """
    Базовый класс для представления события.

    Attributes:
        event_id (int): Уникальный идентификатор события
        creator (User): Создатель события
    """
    event_id: int
    creator: User

    @property
    def title(self):
        raise NotImplementedError("Subclass must define this as a class attribute")

    def request(self):
        raise NotImplementedError("Subclass must implement this abstract method")

    def add_event(self) -> None:
        """Добавляет событие в список событий пользователя."""
        self.request()


@dataclass
class ModelEvent(Event):
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
    text: str
    title: str = "Model request"
    score: float = None
    response: str = None
    amount: int = 0

    def __post_init__(self) -> None:
        self._validate_title()
        self._validate_text()
        self.amount = len(self.text.split())
        self._model = Model()
        self._timestamp: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _validate_title(self) -> None:
        """Проверяет длину названия события."""
        if not 1 <= len(self.title) <= 30:
            raise ValueError("Title must be between 1 and 30 characters")

    def _validate_text(self) -> None:
        """Проверяет длину описания события."""
        if len(self.text) > 300:
            raise ValueError("Text must not exceed 300 characters")

    def request(self):
        """Запись события предсказания модели"""
        if self.amount <= self.creator.balance.balance_value:
            score = self._model.predict(self.text)[0].get("score")
            self.score = score
            self.response = "Yes" if score > 0.5 else "No"
            self.creator.events.append(self)
            self.creator.balance.balance_value -= self.amount
            self.creator.balance.last_update = datetime.now()
        else:
            self.response = "Insufficient funds."
            self.creator.events.append(self)
            raise ValueError("Insufficient funds. Top up your balance.")


@dataclass
class BalanceReplenishmentEvent(Event):
    """
    Класс для представления события пополнения баланса.

    Attributes:
        event_id (int): Уникальный идентификатор события
        creator (User): Создатель события
        title (str): Название события
        amount (int): Сумма пополнения баланса
    """
    title: str = "Balance operation"
    amount: int = 0

    def __post_init__(self) -> None:
        self._validate_title()
        self._timestamp: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _validate_title(self) -> None:
        """Проверяет длину названия события."""
        if not 1 <= len(self.title) <= 30:
            raise ValueError("Title must be between 1 and 30 characters")

    def request(self):
        """Запись события пополнения баланса"""
        self.creator.balance.balance_value += self.amount
        self.creator.balance.last_update = datetime.now()
        self.creator.events.append(self)

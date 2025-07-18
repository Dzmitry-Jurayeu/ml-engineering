from dataclasses import dataclass, field
from datetime import datetime
from typing import List
import re
import bcrypt
from transformers import pipeline
from typing import Union


@dataclass
class User:
    """
    Класс для представления пользователя в системе.

    Attributes:
        user_id (int): Уникальный идентификатор пользователя
        email (str): Email пользователя
        password (str): Пароль пользователя
        balance (Balance): Идентификатор баланса пользователя
        events (List[Event]): Список событий пользователя
    """
    user_id: int
    email: str
    password: str
    balance: 'Balance'
    events: List['Event'] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._validate_email()
        self._validate_password()

    def _validate_email(self) -> None:
        """Проверяет корректность email."""
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if not email_pattern.match(self.email):
            raise ValueError("Invalid email format")

    def _validate_password(self) -> None:
        """Проверяет минимальную длину пароля."""
        if len(self.password) < 8:
            raise ValueError("Password must be at least 8 characters long")

    def _secure_password(self):
        """Хэширование пароля"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(self.password.encode("utf-8"), salt)

    @property
    def _is_admin(self):
        raise NotImplementedError("Subclass must define this as a class attribute")

    def add_event(self, event: Union['ModelEvent', 'BalanceReplenishmentEvent']) -> None:
        """Добавляет событие в список событий пользователя."""
        event.request()

    def check_history(self):
        raise NotImplementedError("Subclass must implement this abstract method")


@dataclass
class CommonUser(User):
    """
    Класс для представления обычного пользователя в системе.

    Attributes:
        user_id (int): Уникальный идентификатор пользователя
        email (str): Email пользователя
        password (str): Пароль пользователя
        balance (int): Баланс пользователя
        events (List[Event]): Список событий пользователя
        _is_admin (bool): Метка о наличии прав администратора
    """

    _is_admin: bool = False

    def check_history(self, number: int = 0):
        """Просмотр последних N запросов и предсказаний пользователя"""
        for event in self.events[-number:]:
            print(event)


@dataclass
class AdminUser(User):
    """
    Класс для представления пользователя с правами администратора в системе.

    Attributes:
        user_id (int): Уникальный идентификатор пользователя
        email (str): Email пользователя
        password (str): Пароль пользователя
        balance (int): Баланс пользователя
        events (List[Event]): Список событий пользователя
        _is_admin (bool): Метка о наличии прав администратора
    """

    _is_admin: bool = True

    def check_history(self, user, number: int = 0):
        """Просмотр последних N запросов и предсказаний пользователя"""
        for event in user.events[-number:]:
            print(event)


@dataclass
class Event:
    """
    Класс для представления события.

    Attributes:
        event_id (int): Уникальный идентификатор события
        creator (User): Создатель события
    """
    event_id: int
    creator: User

    @property
    def title(self):
        raise NotImplementedError("Subclass must define this as a class attribute")


@dataclass
class ModelEvent(Event):
    """
    Класс для представления события.

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
            self.creator.balance.withdraw(self)
        else:
            self.response = "Insufficient funds."
            self.creator.events.append(self)
            raise ValueError("Insufficient funds. Top up your balance.")


@dataclass
class BalanceReplenishmentEvent(Event):
    """
    Класс для представления события.

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
        self.creator.balance.balance_replenishment(self)
        self.creator.events.append(self)


@dataclass
class Balance:
    """
    Класс для представления баланса пользователя.

    Attributes:
        balance_id (int): Уникальный идентификатор баланса
        last_update (datetime): Дата и время последнего изменения баланса
        balance_value (int): Баланс пользователя
    """
    balance_id: int
    last_update: datetime = datetime.now()
    balance_value: int = 0

    def __post_init__(self) -> None:
        self._validate_balance()

    def _validate_balance(self) -> None:
        """Проверяет отрицательность баланса."""
        if self.balance_value < 0:
            raise ValueError("Balance must not be below 0.")

    def balance_replenishment(self, event: 'BalanceReplenishmentEvent') -> None:
        """Пополнение баланса пользователя"""
        self.balance_value += event.amount
        self.last_update = datetime.now()

    def withdraw(self, event: 'ModelEvent') -> None:
        """Списание средств с баланса пользователя"""
        self.balance_value -= event.amount
        self.last_update = datetime.now()


@dataclass
class Model:
    """
    Класс для представления баланса пользователя.

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


def main() -> None:
    try:
        new_id = 1
        balance = Balance(
            balance_id=new_id,
        )
        user = User(
            user_id=new_id,
            email="test_email@gmail.com",
            password="password",
            balance=balance
        )

        model_event = ModelEvent(
            event_id=1,
            creator=user,
            title="Model request",
            text="some polite text",
        )
        balance_event = BalanceReplenishmentEvent(event_id=2, creator=user, amount=10)

        user.add_event(balance_event)
        user.add_event(model_event)
        print(f"Created user: {user}")
        print(f"Number of user events: {len(user.events)}")

    except ValueError as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    main()

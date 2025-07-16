from dataclasses import dataclass, field
from datetime import datetime
from typing import List
import re


@dataclass
class User:
    """
    Класс для представления пользователя в системе.

    Attributes:
        user_id (int): Уникальный идентификатор пользователя
        email (str): Email пользователя
        password (str): Пароль пользователя
        balance (int): Баланс пользователя
        events (List[Event]): Список событий пользователя
    """
    user_id: int
    email: str
    password: str
    balance: int
    events: List['Event'] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._validate_email()
        self._validate_password()
        self._is_admin: bool = False

    def _validate_email(self) -> None:
        """Проверяет корректность email."""
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if not email_pattern.match(self.email):
            raise ValueError("Invalid email format")

    def _validate_password(self) -> None:
        """Проверяет минимальную длину пароля."""
        if len(self.password) < 8:
            raise ValueError("Password must be at least 8 characters long")

    def add_event(self, event: 'Event') -> None:
        """Добавляет событие в список событий пользователя."""
        if event.cost <= self.balance:
            self.events.append(event)
            self.balance -= event.cost
        else:
            raise ValueError("Insufficient funds. Top up your balance.")

    def balance_replenishment(self, amount: int) -> None:
        """Пополнение баланса пользователя"""
        self.balance += amount

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
    """

    def __post_init__(self) -> None:
        self._is_admin: bool = True

    def balance_replenishment(self, user_id: int, amount: int) -> None:
        """Пополнение баланса пользователя"""
        self.balance += amount

    def check_history(self, user_id: int, number: int = 0):
        """Просмотр последних N запросов и предсказаний пользователя"""
        for event in self.events[-number:]:
            print(event)


@dataclass
class Event:
    """
    Класс для представления события.

    Attributes:
        event_id (int): Уникальный идентификатор события
        creator (User): Создатель события
        title (str): Название события
        text (str): Путь к изображению события
        response (str): Результат предсказания модели
        cost (int): Стоимость события
    """
    event_id: int
    creator: User
    title: str
    text: str
    response: str = None

    def __post_init__(self) -> None:
        self._validate_title()
        self._validate_text()
        self.cost: int = len(self.text.split())
        self._timestamp: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _validate_title(self) -> None:
        """Проверяет длину названия события."""
        if not 1 <= len(self.title) <= 30:
            raise ValueError("Title must be between 1 and 30 characters")

    def _validate_text(self) -> None:
        """Проверяет длину описания события."""
        if len(self.text) > 300:
            raise ValueError("Text must not exceed 300 characters")


def main() -> None:
    try:
        user = User(
            user_id=1,
            email="test_email@gmail.com",
            password="password",
            balance=0
        )

        event = Event(
            event_id=1,
            creator=user,
            title="Model request",
            text="some polite text",
        )

        user.balance_replenishment(10)
        user.add_event(event)
        print(f"Created user: {user}")
        print(f"Number of user events: {len(user.events)}")

    except ValueError as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    main()

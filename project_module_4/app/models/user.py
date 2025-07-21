from dataclasses import dataclass, field
from typing import List
import re
import bcrypt
from models.balance import Balance


@dataclass
class User:
    """
    Класс для представления пользователя в системе.

    Attributes:
        user_id (int): Уникальный идентификатор пользователя
        email (str): Email пользователя
        password (str): Пароль пользователя
        balance ('Balance'): Идентификатор баланса пользователя
        events (List[int]): Список событий пользователя
    """
    user_id: int
    email: str
    password: str
    balance: 'Balance'
    events: List[int] = field(default_factory=list)

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
        events (List[int]): Список событий пользователя
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
        events (List[int]): Список событий пользователя
        _is_admin (bool): Метка о наличии прав администратора
    """

    _is_admin: bool = True

    def check_history(self, user, number: int = 0):
        """Просмотр последних N запросов и предсказаний пользователя"""
        for event in user.events[-number:]:
            print(event)

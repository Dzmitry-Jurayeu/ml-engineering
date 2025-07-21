from dataclasses import dataclass
from datetime import datetime
# from models.event import BalanceReplenishmentEvent, ModelEvent


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

    # def balance_replenishment(self, event: 'BalanceReplenishmentEvent') -> None:
    #     """Пополнение баланса пользователя"""
    #     self.balance_value += event.amount
    #     self.last_update = datetime.now()
    #
    # def withdraw(self, event: 'ModelEvent') -> None:
    #     """Списание средств с баланса пользователя"""
    #     self.balance_value -= event.amount
    #     self.last_update = datetime.now()

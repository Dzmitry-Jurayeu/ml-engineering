from models.balance import Balance
from models.event import ModelEvent, BalanceReplenishmentEvent
from models.user import User

if __name__ == '__main__':
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

        balance_event.add_event()
        model_event.add_event()
        print(f"Created user: {user}")
        print(f"Number of user events: {len(user.events)}")

    except ValueError as e:
        print(f"Error: {e}")

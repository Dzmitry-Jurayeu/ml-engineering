from models.event import ModelEvent, BalanceReplenishmentEvent
from models.user import User
from models.model import Model
from database.database import get_settings, init_db, get_database_engine
from loguru import logger
from sqlmodel import Session
from services.crud.user import create_user, get_all_users, get_user_history
from services.crud.balance import balance_replenishment
from services.crud.event import update_model_event
from services.crud.model import get_model_by_params, init_model, add_model

if __name__ == '__main__':
    settings = get_settings()

    init_db(drop_all=True)
    logger.info("Init DB has been success.")

    new_model = Model()

    test_common_user = User(email="test_common@gmail.com", password="testtest")
    test_admin_user = User(email="test_admin@gmail.com", password="testtest", is_admin=True)

    test_balance_event = BalanceReplenishmentEvent(amount=1)
    test_model_event = ModelEvent(text="some polite text")

    test_common_user.balance_events.append(test_balance_event)
    test_common_user.model_events.append(test_model_event)


    engine = get_database_engine()

    with Session(engine) as session:
        add_model(new_model, session)
        model = get_model_by_params(session)
        pipe = init_model(model)
        logger.info("Model loaded.")
        create_user(test_common_user, session)
        logger.info("Common user created.")
        balance_replenishment(test_balance_event, session)
        update_model_event(test_model_event, session, pipe)
        create_user(test_admin_user, session)
        logger.info("Admin user created.")
        user_history = get_user_history(test_admin_user, session)
        users = get_all_users(session)

    for user in users:
        logger.info(f"User: {user}")
        for event in user.balance_events:
            logger.info(f"Event: {event}")

    for enum, event in enumerate(user_history):
        logger.info(f"History element {enum + 1}: {event}")

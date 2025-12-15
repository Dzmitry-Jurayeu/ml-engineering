from models.event import Prediction
from models.user import User
from models.model import Model
from database.database import get_settings, init_db, get_database_engine
from loguru import logger
from sqlmodel import Session
from services.crud.user import create_user, get_user_by_id
from services.crud.event import update_model_event
from services.crud.model import get_model_by_params, init_model, add_model
from services.crud.tank import init_tanks

if __name__ == '__main__':
    settings = get_settings()

    init_db(drop_all=True)
    logger.info("Init DB has been success.")

    new_model = Model()

    demo_common_user = User(user_id=88444060)
    demo_admin_user = User(user_id=10915463, is_admin=True)

    demo_model_event = Prediction()

    demo_common_user.model_events.append(demo_model_event)

    engine = get_database_engine()

    with Session(engine) as session:
        general_df, premium_df = init_tanks(session)
        if not get_user_by_id(88444060, session):
            add_model(new_model, session)
            model = get_model_by_params(session)
            model = init_model(model)
            create_user(demo_common_user, session)
            update_model_event(demo_model_event, session, model, general_df, premium_df)
            create_user(demo_admin_user, session)

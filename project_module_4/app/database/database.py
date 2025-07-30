from sqlmodel import SQLModel, Session, create_engine
from .config import get_settings
from models.event import ModelEvent, BalanceReplenishmentEvent
from models.user import User
from models.model import Model
from services.crud.user import create_user, get_all_users, get_user_history, get_user_by_email
from services.crud.balance import balance_replenishment, balance_withdraw
from services.crud.event import update_model_event
from services.crud.model import get_model_by_params, init_model, add_model

def get_database_engine():
    """
    Create and config the SQLAlchemy engine.

    Returns:
        Engine: Configured SQLAlchemy engine.
    """
    settings = get_settings()

    engine = create_engine(
        url=settings.DATABASE_URL_psycopg,
        echo=settings.DEBUG,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=3600
    )
    return engine

engine = get_database_engine()

def get_session():
    with Session(engine) as session:
        yield session
        
def init_db(drop_all: bool = False) -> None:
    """
    Initialize database schema.

    Args:
        drop_all: If True, drops all tables before creation.

    Raises:
        Exception: Any database-related exception.
    """
    try:
        engine = get_database_engine()
        if drop_all:
            SQLModel.metadata.drop_all(engine)

        SQLModel.metadata.create_all(engine)
        init_demo_data()
    except Exception as e:
        raise

def init_demo_data():
    demo_model = Model()

    demo_common_user = User(email="demo_common@gmail.com", password="demotest")
    demo_admin_user = User(email="demo_admin@gmail.com", password="demotest", is_admin=True)

    demo_balance_event = BalanceReplenishmentEvent(amount=999999)
    demo_model_event = ModelEvent(text="Demo text")

    demo_common_user.balance_events.append(demo_balance_event)
    demo_common_user.model_events.append(demo_model_event)
    with Session(engine) as session:
        if not get_user_by_email("demo_common@gmail.com", session):
            add_model(demo_model, session)
            model = get_model_by_params(session)
            pipe = init_model(model)
            create_user(demo_common_user, session)
            balance_replenishment(demo_balance_event, session)
            update_model_event(demo_model_event, session, pipe)
            create_user(demo_admin_user, session)
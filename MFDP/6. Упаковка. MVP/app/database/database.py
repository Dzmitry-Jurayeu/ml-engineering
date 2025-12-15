from sqlmodel import SQLModel, Session, create_engine
from .config import get_settings
from models.event import Prediction
from models.user import User
from models.model import Model
from services.crud.user import create_user, get_user_by_id
from services.crud.event import update_model_event
from services.crud.model import get_model_by_params, init_model, add_model
from services.crud.tank import init_tanks

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
        
def init_db(drop_all: bool = False):
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
        general_df, premium_df = init_demo_data()
        return general_df, premium_df
    except Exception as e:
        raise

def init_demo_data():
    demo_model = Model()

    demo_common_user = User(user_id=88444060)
    demo_admin_user = User(user_id=10915463, is_admin=True)

    demo_model_event = Prediction()

    demo_common_user.model_events.append(demo_model_event)
    with Session(engine) as session:
        general_df, premium_df = init_tanks(session)
        if not get_user_by_id(88444060, session):
            add_model(demo_model, session)
            model = get_model_by_params(session)
            model = init_model(model)
            create_user(demo_common_user, session)
            update_model_event(demo_model_event, session, model, general_df, premium_df)
            create_user(demo_admin_user, session)
    return general_df, premium_df
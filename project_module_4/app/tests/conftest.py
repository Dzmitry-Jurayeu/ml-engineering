import pytest
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool
from api import app
from database.database import get_session
from fastapi.testclient import TestClient
from routes.user import get_current_active_user
from routes.api_models import UserOut


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///testing.db", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="drop_session")
def drop_session_fixture():
    engine = create_engine("sqlite:///testing.db", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="client_admin")
def client_admin_fixture(session: Session):
    def get_session_override():
        return session

    admin_user = UserOut(
        user_id=1,
        email="test_email_admin@gmail.com",
        password="my_secret_password",
        is_admin=True
    )
    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_current_active_user] = lambda: admin_user

    client = TestClient(app)
    client.user_id = admin_user.user_id

    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="client_common")
def client_common_fixture(session: Session):
    def get_session_override():
        return session

    common_user = UserOut(
        user_id=2,
        email="test_email_common@gmail.com",
        password="my_secret_password",
        is_admin=False
    )
    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_current_active_user] = lambda: common_user

    client = TestClient(app)
    client.user_id = common_user.user_id

    yield client
    app.dependency_overrides.clear()

import pytest

from datetime import datetime
from sqlalchemy.orm import Session


with pytest.MonkeyPatch.context() as monkeypatch:
    # random api token in the test environment to test authentication
    monkeypatch.setenv("AUTH_API_KEY", "random-test-token")

    from robot_cleaner import db
    from robot_cleaner.app import create_app
    from robot_cleaner.models import (
        Base,
        Execution,
    )


@pytest.fixture
def init_db(monkeypatch):
    """
    Initialize test db.
    Create before tests & drop after tests.
    """
    Base.metadata.drop_all(bind=db.engine)
    Base.metadata.create_all(bind=db.engine)
    yield
    Base.metadata.drop_all(bind=db.engine)


@pytest.fixture
def app(monkeypatch):
    app = create_app()
    yield app


@pytest.fixture
def auth_app(monkeypatch):
    monkeypatch.setenv("IS_PRODUCTION", "True")
    app = create_app(is_production=True)
    yield app


@pytest.fixture
def database(init_db):
    """
    Populate test db with test records.
    """
    with db.Session() as session:
        session: Session

        execution_1 = Execution(
            commands=2,
            result=4,
            duration=0.000123,
            timestamp=datetime.now(),
        )

        session.add(execution_1)
        session.commit()
        session.refresh(execution_1)

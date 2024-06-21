import backoff

from functools import wraps
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

from robot_cleaner import config


engine = create_engine(config.SQLALCHEMY_URI)
Session = sessionmaker(engine)


def db_session(func):
    """
    Use this decorator to pass a session object to the wrapped `func`.
    """
    @backoff.on_exception(
        backoff.expo,
        OperationalError,
        max_tries=3,
        max_time=30,
    )
    @wraps(func)
    def wrapper(*args, **kwargs):
        with Session() as session:
            return func(*args, session=session, **kwargs)

    return wrapper

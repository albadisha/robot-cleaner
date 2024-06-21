import sqlalchemy as sa

from sqlalchemy.orm import Session
from datetime import datetime, timezone

from robot_cleaner.models.base import Base


class Execution(Base):
    """
    Represents robot's cleaning executions.
    """

    __tablename__ = "executions"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    commands = sa.Column(sa.Integer)
    result = sa.Column(sa.Integer, nullable=False)
    duration = sa.Column(sa.Float)
    timestamp = sa.Column(sa.DateTime, default=datetime.now(timezone.utc))


def add_execution(
    session: Session,
    commands: int,
    result: int,
    duration: float,
) -> Execution:
    execution = Execution(
        commands=commands,
        result=result,
        duration=duration
    )
    session.add(execution)
    session.commit()
    return fetch_execution(session, execution)


def fetch_execution(
    session: Session, execution: Execution,
) -> Execution:
    return (
        session.query(Execution)
        .filter(
            Execution.id == execution.id,
        )
        .first()
    )

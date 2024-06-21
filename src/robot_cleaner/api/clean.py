import time
import typing

from enum import Enum
from flask import jsonify, request
from sqlalchemy.orm import Session
from werkzeug.exceptions import BadRequest

from robot_cleaner.db import db_session
from robot_cleaner.models.execution import (
    Execution, add_execution,
)


MOVE_MAP = {
    "north": {
        "x": 0,
        "y": 1,
    },
    "south": {
        "x": 0,
        "y": -1,
    },
    "east": {
        "x": 1,
        "y": 0,
    },
    "west": {
        "x": -1,
        "y": 0,
    },
}


class Direction(str, Enum):
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"


class Coordinates(typing.TypedDict):
    x: int
    y: int


class Directions(typing.TypedDict):
    direction: Direction
    steps: int


class MovingPath(typing.TypedDict):
    """
    Represents robot's moving path.
    """
    start: Coordinates
    commands: typing.List[Directions]


def serialize_execution(execution: Execution):
    return {
        "commands": execution.commands,
        "result": execution.result,
        "duration": execution.duration,
        "timestamp": execution.timestamp,
        "uri": f"/tibber-developer-test/enter-path/{execution.id}",
    }


@db_session
def execute_cleaning(session: Session):
    """
    POST tibber-developer-test/enter-path API
    """
    data = request.get_json()
    validate_request_data(data)

    timestamp1 = time.time()
    result = calculate_unique_places(data)
    timestamp2 = time.time()

    execution = add_execution(
        session,
        commands=len(data.get("commands")),
        result=result,
        duration=round(timestamp2 - timestamp1, 6)
    )
    return jsonify(serialize_execution(execution))


def calculate_unique_places(data: MovingPath):
    """
    Return the number of unique vertices the robot's path followed.
    """
    if len(data.get("commands")) == 0:
        return 1

    unique_places = set()

    x = data.get("start").get("x")
    y = data.get("start").get("y")

    unique_places.add((x, y))

    for command in data.get("commands"):
        steps = command.get("steps")
        while steps > 0:
            x, y = move(
                x,
                y,
                command.get("direction"),
            )
            unique_places.add((x, y))
            steps -= 1
    return len(unique_places)


def move(x: int, y: int, direction: Direction):
    """
    Move along x, y axis depending on direction.
    """
    x += MOVE_MAP[direction]["x"]
    y += MOVE_MAP[direction]["y"]
    return x, y


def validate_request_data(data: MovingPath):
    if data is None or not isinstance(data, dict):
        raise BadRequest(f"Invalid data: {data}. Data should be valid json.")

    x = data.get("start").get("x")
    if not -100000 <= x <= 100000:
        raise BadRequest(f"x value out of bounds: {x}")

    y = data.get("start").get("y")
    if not -100000 <= y <= 100000:
        raise BadRequest(f"y value out of bounds: {y}")

    if len(data.get("commands")) > 10000:
        raise BadRequest(
            "Number of commands should be lower",
            f" than 10000: {len(data.get("commands"))}"
        )

    for command in data.get("commands"):
        if command.get("direction") not in MOVE_MAP.keys():
            raise BadRequest(
                "Direction value should be one of: (north, south, east, west)",
            )
        if not 0 < command.get("steps") < 100000:
            raise BadRequest(
                f"Steps value is out of bounds: {command.get("steps")}",
            )

import time
import typing

from enum import Enum
from flask import jsonify, request
from sqlalchemy.orm import Session
from sortedcontainers import SortedList
from werkzeug.exceptions import BadRequest

from robot_cleaner.db import db_session
from robot_cleaner.models.execution import (
    Execution,
    add_execution,
)


MOVE_MAP = {
    "north": (0, 1),
    "south": (0, -1),
    "east": (1, 0),
    "west": (-1, 0),
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
        duration=round(timestamp2 - timestamp1, 6),
    )
    return jsonify(serialize_execution(execution))


def calculate_unique_places(data: MovingPath):
    """
    Return the number of unique vertices the robot's path followed.
    """
    if len(data.get("commands")) == 0:
        return 1

    horizontal_lines, vertical_lines = divide_path(data)

    merged_vertical_lines = merge_overlapping(vertical_lines, axis=0)
    merged_horizontal_lines = merge_overlapping(horizontal_lines, axis=1)

    common = count_intersections(
        merged_vertical_lines,
        merged_horizontal_lines,
    )

    total = count_points(merged_vertical_lines) + count_points(
        merged_horizontal_lines
    )  # noqa

    return total - common


def divide_path(data: MovingPath):
    """
    Divide given path into lists of vertical and horizontal segments.
    A segment endpoints are expressed as a tuple of tuples: ((a, b), (c, d)).
    """
    horizontal_lines = []
    vertical_lines = []

    x = data.get("start").get("x")
    y = data.get("start").get("y")

    for command in data.get("commands"):
        direction = command.get("direction")
        steps = command.get("steps")
        dx, dy = MOVE_MAP[direction]

        x_next, y_next = x + dx * steps, y + dy * steps
        (
            vertical_lines.append(((x, y), (x_next, y_next)))
            if dx == 0
            else horizontal_lines.append(((x, y), (x_next, y_next)))
        )
        x, y = x_next, y_next

    return horizontal_lines, vertical_lines


def merge_overlapping(segments, axis=None):
    """
    Merge overlapping or continuous segments on the same axis.
    """
    if len(segments) == 0:
        return []

    # Sort each segment's points
    segments = [(tuple(sorted(seg))) for seg in segments]

    # Sort segments based on axis
    (
        segments.sort(key=lambda segment: (segment[0][0], segment[0][1]))
        if axis == 0
        else segments.sort(key=lambda segment: (segment[0][1], segment[0][0]))
    )

    merged_segments = [segments[0]]

    for segment in segments[1:]:
        last_merged = merged_segments[-1]
        # last merged segment coordinates
        l_x1, l_y1 = last_merged[0]
        l_x2, l_y2 = last_merged[1]
        # current segment coordinates
        c_x1, c_y1 = segment[0]
        c_x2, c_y2 = segment[1]

        if axis == 0:  # Vertical segments
            if l_x1 == c_x1 and c_y1 <= l_y2:  # same_x & overlapping_y
                merged_segments[-1] = (
                    (l_x1, min(l_y1, c_y1)),
                    (l_x2, max(l_y2, c_y2)),
                )
                continue

        if axis == 1:  # Horizontal segments
            if l_y1 == c_y1 and c_x1 <= l_x2:  # same_y & overlapping_x
                merged_segments[-1] = (
                    (min(l_x1, c_x1), l_y1),
                    (max(l_x2, c_x2), l_y2),
                )
                continue

        merged_segments.append(segment)

    return merged_segments


def count_intersections(vertical_segments, horizontal_segments):
    """
    Sweep Line Algorithm.
    Count intersections between vertical and horizontal segments.
    Continuous line points are counted as an intersection.
    """
    if len(vertical_segments) == 0 or len(horizontal_segments) == 0:
        return 0

    events = []

    for (x, y1), (x, y2) in vertical_segments:
        if y1 > y2:
            y1, y2 = y2, y1
        events.append((x, y1, y2, "v"))

    for (x1, y), (x2, y) in horizontal_segments:
        if x1 > x2:
            x1, x2 = x2, x1
        events.append((x1, y, y, "h_start"))
        events.append((x2, y, y, "h_end"))

    events.sort(key=lambda e: (e[0], e[3] != "h_start", e[3] == "h_end"))

    active_horizontal_segments = SortedList()
    num_intersections = 0

    for _, y1, y2, event_type in events:
        if event_type == "h_start":
            active_horizontal_segments.add(y1)
        elif event_type == "h_end":
            active_horizontal_segments.remove(y1)
        elif event_type == "v":
            intersections = active_horizontal_segments.bisect_right(
                y2
            ) - active_horizontal_segments.bisect_left(y1)
            num_intersections += intersections

    return num_intersections


def count_points(lines: typing.List[tuple]):
    """
    Count number of vertices of multiple horizontal/vertical segments.
    """
    if len(lines) == 0:
        return 0
    count = 0
    for start, end in lines:
        count += count_segment_points(start, end)
    return count


def count_segment_points(a: typing.Tuple, b: typing.Tuple):
    """
    Count number of vertices that a vertical/horizontal segment passes through.
    The segment starts at point a(x, y) and ends at point b(x, y).
    """
    ax, ay = abs(a[0]), abs(a[1])
    bx, by = abs(b[0]), abs(b[1])

    if ax == bx:
        return abs(by - ay) + 1
    if ay == by:
        return abs(bx - ax) + 1
    return 0


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
            f"Number of commands should be lower than 10000: {len(data.get("commands"))}"  # noqa
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

from robot_cleaner.db import Session
from robot_cleaner.models import Execution
from robot_cleaner.api.clean import (
    calculate_unique_places,
    merge_overlapping,
    count_intersections,
    count_segment_points,
    divide_path,
)


def test_execute_cleaning(app, database):
    """
    Simple examples to test that api works as expected.
    """
    request_body = {
        "start": {
            "x": 10,
            "y": 22,
        },
        "commands": [
            {"direction": "east", "steps": 2},
            {"direction": "north", "steps": 1},
        ],
    }
    response = app.test_client().post(
        "tibber-developer-test/enter-path", json=request_body
    )

    assert response.status_code == 200
    assert response.json["result"] == 4
    assert response.json["commands"] == len(request_body["commands"])
    assert response.json["timestamp"] is not None
    assert response.json["duration"] is not None

    # id=2 since one record already exists in test db
    assert response.json["uri"] == "/tibber-developer-test/enter-path/2"

    request_body = {
        "start": {
            "x": 10,
            "y": 22,
        },
        "commands": [
            {"direction": "east", "steps": 2},
            {"direction": "north", "steps": 1},
            {"direction": "west", "steps": 3},
        ],
    }
    response = app.test_client().post(
        "tibber-developer-test/enter-path", json=request_body
    )

    assert response.status_code == 200
    assert response.json["result"] == 7
    assert response.json["commands"] == len(request_body["commands"])


def test_execute_cleaning_db_insertion(app, database):
    """
    Test record creation in db.
    """
    request_body = {
        "start": {
            "x": 10,
            "y": 22,
        },
        "commands": [
            {"direction": "east", "steps": 2},
            {"direction": "north", "steps": 1},
        ],
    }

    with Session() as session:
        executions = session.query(Execution).all()
        assert len(executions) == 1  # no. of existing executions in test db

        response = app.test_client().post(
            "tibber-developer-test/enter-path", json=request_body
        )
        assert response.status_code == 200

        executions = session.query(Execution).all()
        assert len(executions) == 2


def test_execute_cleaning_complex_directions(app, database):
    """
    Test multiple direction commands.
    """
    request_body = {
        "start": {
            "x": -2,
            "y": 1,
        },
        "commands": [
            {"direction": "south", "steps": 1},
            {"direction": "north", "steps": 2},
            {"direction": "east", "steps": 1},
            {"direction": "west", "steps": 2},
            {"direction": "west", "steps": 2},
            {"direction": "north", "steps": 1},
            {"direction": "east", "steps": 2},
        ],
    }
    response = app.test_client().post(
        "tibber-developer-test/enter-path", json=request_body
    )
    assert response.status_code == 200
    assert response.json["result"] == 10
    assert response.json["commands"] == len(request_body["commands"])


def test_execute_cleaning_repeat_path(app, database):
    """
    Test the api to only count unique places.
    """
    request_body = {
        "start": {
            "x": 1,
            "y": 2,
        },
        "commands": [
            {"direction": "south", "steps": 2},
            {"direction": "north", "steps": 2},
        ],
    }
    response = app.test_client().post(
        "tibber-developer-test/enter-path", json=request_body
    )

    assert response.status_code == 200
    assert response.json["result"] == 3
    assert response.json["commands"] == len(request_body["commands"])


def test_execute_cleaning_negative_input(app, database):
    """
    Test negative starting coordinates.
    """
    request_body = {
        "start": {
            "x": -202,
            "y": -400,
        },
        "commands": [
            {"direction": "south", "steps": 100},
            {"direction": "north", "steps": 50},
            {"direction": "east", "steps": 7},
            {"direction": "west", "steps": 14},
        ],
    }
    response = app.test_client().post(
        "tibber-developer-test/enter-path", json=request_body
    )

    assert response.status_code == 200
    assert response.json["result"] == 115
    assert response.json["commands"] == len(request_body["commands"])


def test_execute_cleaning_bad_request_data(app, database):
    """
    Test invalid input.
    """
    request_body = {
        "start": {
            "x": 10,
            "y": 22,
        },
        "commands": [
            {"direction": "east", "steps": -22},
        ],
    }
    response = app.test_client().post(
        "tibber-developer-test/enter-path", json=request_body
    )
    assert response.status_code == 400

    request_body = {
        "start": {
            "x": 10,
            "y": 22,
        },
        "commands": [
            {"direction": "mess", "steps": 2},
        ],
    }
    response = app.test_client().post(
        "tibber-developer-test/enter-path", json=request_body
    )
    assert response.status_code == 400

    request_body = {
        "start": {
            "x": 200000,
            "y": 22,
        },
        "commands": [
            {"direction": "east", "steps": 2},
        ],
    }
    response = app.test_client().post(
        "tibber-developer-test/enter-path", json=request_body
    )
    assert response.status_code == 400

    request_body = {
        "start": {
            "x": 0,
            "y": -200000,
        },
        "commands": [
            {"direction": "east", "steps": 2},
        ],
    }
    response = app.test_client().post(
        "tibber-developer-test/enter-path", json=request_body
    )
    assert response.status_code == 400


def test_execute_cleaning_bad_request_body(app, database):
    """
    Test invalid headers/request body.
    """
    HEADERS = {"Content-Type": "application/json"}
    request_body = "steps"
    response = app.test_client().post(
        "tibber-developer-test/enter-path", headers=HEADERS, json=request_body
    )
    assert response.status_code == 400

    HEADERS = {"Content-Type": "plain/text"}
    request_body = "steps"
    response = app.test_client().post(
        "tibber-developer-test/enter-path", headers=HEADERS, json=request_body
    )
    assert response.status_code == 415


def test_calculate_unique_places():
    # empty commands list
    data = {
        "start": {
            "x": 1,
            "y": 1,
        },
        "commands": [],
    }
    assert calculate_unique_places(data) == 1

    # 0 steps commands
    data = {
        "start": {
            "x": 1,
            "y": 1,
        },
        "commands": [
            {"direction": "east", "steps": 0},
            {"direction": "north", "steps": 0},
        ],
    }
    assert calculate_unique_places(data) == 1

    # complex paths
    data = {
        "start": {
            "x": 0,
            "y": 0,
        },
        "commands": [
            {"direction": "east", "steps": 2},
            {"direction": "north", "steps": 2},
            {"direction": "east", "steps": 2},
            {"direction": "west", "steps": 1},
            {"direction": "west", "steps": 2},
            {"direction": "east", "steps": 4},
            {"direction": "south", "steps": 1},
            {"direction": "west", "steps": 4},
            {"direction": "north", "steps": 1},
        ],
    }
    assert calculate_unique_places(data) == 13

    data = {
        "start": {
            "x": 0,
            "y": 0,
        },
        "commands": [
            {"direction": "east", "steps": 2},
            {"direction": "north", "steps": 2},
            {"direction": "east", "steps": 2},
            {"direction": "west", "steps": 1},
            {"direction": "west", "steps": 2},
            {"direction": "east", "steps": 4},
            {"direction": "south", "steps": 1},
            {"direction": "west", "steps": 4},
            {"direction": "north", "steps": 3},
            {"direction": "east", "steps": 1},
            {"direction": "south", "steps": 4},
            {"direction": "east", "steps": 1},
            {"direction": "north", "steps": 3},
            {"direction": "west", "steps": 1},
            {"direction": "north", "steps": 1},
            {"direction": "west", "steps": 1},
        ],
    }
    assert calculate_unique_places(data) == 19


def test_divide_path():
    # test empty commands list
    data = {"start": {"x": 0, "y": 0}, "commands": []}
    result = divide_path(data)
    assert result == ([], [])

    # test single command horizontal line
    data = {
        "start": {"x": 0, "y": 0},
        "commands": [{"direction": "east", "steps": 5}],
    }  # noqa
    expected_horizontal = [((0, 0), (5, 0))]
    expected_vertical = []
    result = divide_path(data)
    assert result == (expected_horizontal, expected_vertical)

    # test single command vertical line
    data = {
        "start": {"x": 0, "y": 0},
        "commands": [{"direction": "north", "steps": 5}],
    }  # noqa
    expected_horizontal = []
    expected_vertical = [((0, 0), (0, 5))]
    result = divide_path(data)
    assert result == (expected_horizontal, expected_vertical)

    # test multiple commands
    data = {
        "start": {"x": 0, "y": 0},
        "commands": [
            {"direction": "east", "steps": 5},
            {"direction": "north", "steps": 5},
            {"direction": "west", "steps": 3},
            {"direction": "south", "steps": 2},
        ],
    }
    expected_horizontal = [((0, 0), (5, 0)), ((5, 5), (2, 5))]
    expected_vertical = [((5, 0), (5, 5)), ((2, 5), (2, 3))]
    result = divide_path(data)
    assert result == (expected_horizontal, expected_vertical)

    # test multiple mixed commands
    data = {
        "start": {"x": 0, "y": 0},
        "commands": [
            {"direction": "east", "steps": 3},
            {"direction": "north", "steps": 4},
            {"direction": "west", "steps": 3},
            {"direction": "south", "steps": 4},
            {"direction": "east", "steps": 4},
            {"direction": "west", "steps": 3},
            {"direction": "west", "steps": 1},
            {"direction": "south", "steps": 6},
        ],
    }
    expected_horizontal = [
        ((0, 0), (3, 0)),
        ((3, 4), (0, 4)),
        ((0, 0), (4, 0)),
        ((4, 0), (1, 0)),
        ((1, 0), (0, 0)),
    ]
    expected_vertical = [((3, 0), (3, 4)), ((0, 4), (0, 0)), ((0, 0), (0, -6))]
    result = divide_path(data)
    assert result == (expected_horizontal, expected_vertical)


def test_merge_overlapping():
    # test merge vertical segments
    segments = [((-202, -400), (-202, -500)), ((-202, -500), (-202, -450))]
    expected_output = [((-202, -500), (-202, -400))]
    output = merge_overlapping(segments, axis=0)
    assert output == expected_output

    # test merge horizontal segments
    segments = [((-202, -450), (-195, -450)), ((-195, -450), (-209, -450))]
    expected_output = [((-209, -450), (-195, -450))]
    output = merge_overlapping(segments, axis=1)
    assert output == expected_output

    # test no merge needed on vertical segments
    segments = [
        ((0, 0), (0, 1)),
        ((1, 0), (1, 1)),
        ((5, 10), (5, 8)),
        ((3, 11), (3, 2)),
    ]
    expected_output = [
        ((0, 0), (0, 1)),
        ((1, 0), (1, 1)),
        ((3, 2), (3, 11)),
        ((5, 8), (5, 10)),
    ]
    output = merge_overlapping(segments, axis=0)
    assert output == expected_output

    # test no merge needed on horizontal segments
    segments = [
        ((0, 0), (1, 0)),
        ((0, 1), (1, 1)),
        ((5, 6), (7, 6)),
        ((10, 3), (8, 3)),
    ]
    expected_output = [
        ((0, 0), (1, 0)),
        ((0, 1), (1, 1)),
        ((8, 3), (10, 3)),
        ((5, 6), (7, 6)),
    ]
    output = merge_overlapping(segments, axis=1)
    assert output == expected_output

    # test complex merge on vertical segments
    segments = [((1, 1), (1, 5)), ((1, 3), (1, 7)), ((1, 6), (1, 8))]
    expected_output = [((1, 1), (1, 8))]
    output = merge_overlapping(segments, axis=0)
    assert output == expected_output

    # test complex merge on horizontal segments
    segments = [((1, 1), (5, 1)), ((3, 1), (7, 1)), ((6, 1), (8, 1))]
    expected_output = [((1, 1), (8, 1))]
    output = merge_overlapping(segments, axis=1)
    assert output == expected_output

    # test mixed coordinates on vertical segments
    segments = [((0, 1), (0, 0)), ((0, 0), (0, -1)), ((0, 2), (0, -4))]
    expected_output = [((0, -4), (0, 2))]
    output = merge_overlapping(segments, axis=0)
    assert output == expected_output

    # test mixed coordinates on horizontal segments
    segments = [((1, 0), (0, 0)), ((0, 0), (-1, 0)), ((0, 0), (-2, 0))]
    expected_output = [((-2, 0), (1, 0))]
    output = merge_overlapping(segments, axis=1)
    assert output == expected_output

    # test continuous merge on vertical segments
    segments = [((0, 1), (0, 0)), ((0, 0), (0, -1)), ((0, -1), (0, -4))]
    expected_output = [((0, -4), (0, 1))]
    output = merge_overlapping(segments, axis=0)
    assert output == expected_output

    # test continuous merge on horizontal segments
    segments = [((1, 0), (0, 0)), ((0, 0), (-1, 0)), ((1, 0), (3, 0))]
    expected_output = [((-1, 0), (3, 0))]
    output = merge_overlapping(segments, axis=1)
    assert output == expected_output


def test_count_intersections():
    # test no intersections
    vertical_segments = [((0, 0), (0, 1))]
    horizontal_segments = [((1, 1), (2, 1))]
    count = count_intersections(vertical_segments, horizontal_segments)
    assert count == 0

    # test single intersection
    vertical_segments = [((1, 0), (1, 2))]
    horizontal_segments = [((0, 1), (2, 1))]
    count = count_intersections(vertical_segments, horizontal_segments)
    assert count == 1

    # test multiple intersections
    vertical_segments = [
        ((1, 0), (1, 3)),
        ((3, 0), (3, 3)),
        ((4, 1), (4, 2)),
    ]
    horizontal_segments = [
        ((0, 1), (4, 1)),
        ((0, 2), (4, 2)),
        ((3, 3), (4, 3)),
    ]
    count = count_intersections(vertical_segments, horizontal_segments)
    assert count == 7

    # test vertical on horizontal segment
    vertical_segments = [((2, 1), (2, 3))]
    horizontal_segments = [((0, 2), (5, 2))]
    count = count_intersections(vertical_segments, horizontal_segments)
    assert count == 1

    # test no vertical segments
    vertical_segments = []
    horizontal_segments = [((0, 2), (5, 2))]
    count = count_intersections(vertical_segments, horizontal_segments)
    assert count == 0

    # test no horizontal segments
    vertical_segments = [((2, 1), (2, 3))]
    horizontal_segments = []
    count = count_intersections(vertical_segments, horizontal_segments)
    assert count == 0

    # test intersections with negative coordinates
    vertical_segments = [((-2, -3), (-2, 2)), ((-1, -1), (-1, 1))]
    horizontal_segments = [((-3, 0), (0, 0)), ((-3, -2), (0, -2))]
    count = count_intersections(vertical_segments, horizontal_segments)
    assert count == 3

    # test intersections with mixed coordinates
    vertical_segments = [
        ((0, -1), (0, 1)),
        ((-1, 0), (-1, 2)),
        ((2, 0), (2, 3)),
    ]
    horizontal_segments = [
        ((1, 0), (3, 0)),
        ((-2, 1), (1, 1)),
        ((-1, -1), (1, -1)),
    ]
    count = count_intersections(vertical_segments, horizontal_segments)
    assert count == 4


def test_count_segment_points():
    # test vertical positive pointd
    assert count_segment_points((0, 0), (0, 5)) == 6
    assert count_segment_points((3, 1), (3, 4)) == 4
    assert count_segment_points((1, 1), (1, 1)) == 1

    # test vertical negative points
    assert count_segment_points((0, 0), (0, -5)) == 6
    assert count_segment_points((-3, -1), (-3, -4)) == 4

    # test horizontal positive points
    assert count_segment_points((0, 0), (5, 0)) == 6
    assert count_segment_points((1, 2), (4, 2)) == 4

    # test horizontal negative points
    assert count_segment_points((0, 0), (-5, 0)) == 6
    assert count_segment_points((-1, -2), (-4, -2)) == 4

    # test mixed positive and negative points
    assert count_segment_points((0, 0), (0, 0)) == 1
    assert count_segment_points((0, 5), (0, 0)) == 6
    assert count_segment_points((5, 0), (0, 0)) == 6
    assert count_segment_points((0, 0), (5, 0)) == 6

    # test non aligned points
    assert count_segment_points((0, 0), (5, 5)) == 0
    assert count_segment_points((3, 4), (7, 8)) == 0

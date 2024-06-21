from robot_cleaner.db import Session
from robot_cleaner.models import Execution
from robot_cleaner.api.clean import calculate_unique_places, move, Direction


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
    """
    Test calculate_unique_places function with empty command list.
    """
    data = {
        "start": {
            "x": 2,
            "y": 2,
        },
        "commands": [],
    }

    unique_places = calculate_unique_places(data)
    assert unique_places == 1


def test_move():
    """
    Test move function.
    """
    x, y = move(1, -200, Direction.NORTH)
    assert x == 1
    assert y == -199

    x, y = move(-1, 200, Direction.SOUTH)
    assert x == -1
    assert y == 199

    x, y = move(1, 50, Direction.EAST)
    assert x == 2
    assert y == 50

    x, y = move(23, 2, Direction.WEST)
    assert x == 22
    assert y == 2

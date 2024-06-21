HEADERS = {"Authorization": "Bearer random-test-token"}
UNAUTH_HEADERS = {"Authorization": "Bearer token-invalid"}


def test_health_ok(auth_app, database):
    response = auth_app.test_client().get("/_health")
    assert response.status_code == 200


def test_execute_cleaning_unauthorized(auth_app, database):
    response = auth_app.test_client().post(
        "/tibber-developer-test/enter-path",
        json={"start": {"x": 1, "y": 2}, "commands": []}
    )
    assert response.status_code == 401


def test_execute_cleaning_authorized(auth_app, database):
    response = auth_app.test_client().post(
        "/tibber-developer-test/enter-path",
        headers=HEADERS,
        json={"start": {"x": 1, "y": 2}, "commands": []}
    )
    assert response.status_code == 200
    assert response.json


def test_execute_cleaning_unauthorized_token(auth_app, database):
    response = auth_app.test_client().post(
        "/tibber-developer-test/enter-path",
        headers=UNAUTH_HEADERS,
        json={"start": {"x": 1, "y": 2}, "commands": []}
    )
    assert response.status_code == 401

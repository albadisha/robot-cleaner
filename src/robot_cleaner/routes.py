import flask

from robot_cleaner.api import clean


def _health():
    return "OK", 200


def register_routes(app: flask.Flask):
    # health endpoint
    app.add_url_rule("/_health", view_func=_health)

    # clean endpoint
    app.add_url_rule(
        "/tibber-developer-test/enter-path",
        view_func=clean.execute_cleaning,
        methods=["POST"],
    )

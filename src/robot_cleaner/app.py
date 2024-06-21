from flask import Flask

from robot_cleaner import auth
from robot_cleaner import routes
from robot_cleaner import config


def create_app(is_production=False):
    app = Flask("robot_cleaner")
    app.config.from_pyfile("config.py")

    routes.register_routes(app)
    auth.AuthMiddleware(app, is_production=is_production)
    return app


app = create_app(is_production=config.IS_PRODUCTION)
application = app

import structlog

from flask import Flask, request
from werkzeug.exceptions import Unauthorized

from robot_cleaner import config


logger = structlog.get_logger()


class AuthMiddleware:
    def __init__(self, app: Flask, is_production=True):
        self.token = config.AUTH_API_KEY
        self.dev = not is_production

        app.before_request(self.handle_auth)

    def handle_auth(self):
        if self.dev:
            logger.warning("Running in DEV mode. Skipping authentication!")
            return

        if request.path == "/_health":
            return

        auth_header = request.headers.get("Authorization", "")
        if auth_header == "":
            raise Unauthorized("Empty authorization header!")

        token = auth_header.split()[-1]
        if token != self.token:
            raise Unauthorized("Invalid API token!")

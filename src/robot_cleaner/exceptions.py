import traceback

from flask import jsonify, Flask
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException


def register_error_handlers(app: Flask):
    app.register_error_handler(IntegrityError, _handle_integrity_errors)
    app.register_error_handler(Exception, _handle_http_error)


def _handle_integrity_errors(exc: IntegrityError):
    traceback.print_exception(exc)
    return jsonify({"details": "Resource already exists"}), 400


def _handle_http_error(exc: Exception):
    if isinstance(exc, HTTPException):
        return jsonify({"details": exc.description}), exc.code

    traceback.print_exception(exc)

    return jsonify({"details": "Internal server error"}), 500

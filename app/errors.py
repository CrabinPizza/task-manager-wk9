"""Application errors. Services raise these; routes never build error responses by hand."""

from flask import jsonify


class AppError(Exception):
    """Base class for errors that map to an HTTP response."""

    status_code = 500

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class ValidationError(AppError):
    """Bad input from the client."""

    status_code = 400


class NotFoundError(AppError):
    """The requested resource does not exist."""

    status_code = 404


def register_error_handlers(app):
    """Turn AppError subclasses into JSON error responses."""

    @app.errorhandler(AppError)
    def handle_app_error(error):
        return jsonify({"error": error.message}), error.status_code

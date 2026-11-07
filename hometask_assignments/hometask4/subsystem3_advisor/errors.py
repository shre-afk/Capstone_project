"""Exceptions and Flask error handling for the advisor subsystem."""

from flask import current_app, jsonify
from werkzeug.exceptions import HTTPException


class AdvisorError(Exception):
    status_code = 500


class SummaryNotFoundError(AdvisorError):
    status_code = 404


class InvalidSummaryError(AdvisorError):
    status_code = 422


class AdvisorDatabaseError(AdvisorError):
    status_code = 503


class AdvisorErrorHandler:
    def __init__(self, app):
        app.register_error_handler(AdvisorError, self.handle_advisor_error)
        app.register_error_handler(HTTPException, self.handle_http_error)
        app.register_error_handler(Exception, self.handle_unexpected_error)

    def handle_advisor_error(self, error):
        message = str(error)
        if error.status_code >= 500:
            current_app.logger.error('Advisor subsystem failure', exc_info=error)
            message = 'Energy advisor data is temporarily unavailable.'
        return jsonify(error=type(error).__name__, message=message), error.status_code

    def handle_http_error(self, error):
        return jsonify(error=error.name, message=error.description), error.code

    def handle_unexpected_error(self, error):
        current_app.logger.error('Unexpected advisor failure', exc_info=error)
        return jsonify(error='InternalError', message='An unexpected error occurred.'), 500

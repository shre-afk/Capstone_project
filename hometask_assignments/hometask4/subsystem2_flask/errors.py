"""Everything that can go wrong in Subsystem 2 (Data & Analytics) and how we answer it"""
 
from flask import current_app, jsonify
 
 
class DataSubsystemError(Exception):
    """Parent of all our errors - Catch this one and we catch every child below"""
 
    status_code = 500
 
    def __init__(self, message, details=None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
 
    def to_dict(self):
        return {"error": type(self).__name__, "message": self.message, "details": self.details}
 
 
class ValidationError(DataSubsystemError):
    status_code = 400        # the client sent something wrong
 
 
class NotFoundError(DataSubsystemError):
    status_code = 404        # that building or meter doesn't exist
 
 
class DuplicateReadingError(DataSubsystemError):
    status_code = 409        # "conflict": that slot already has a reading
 
 
class DatabaseUnavailableError(DataSubsystemError):
    status_code = 503        # our fault: MySQL is down or unreachable
 
 
class DataErrorHandler:
    """Plugs into Flask and turns our exceptions into tidy JSON answers."""
 
    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)
 
    def init_app(self, app):
        app.register_error_handler(DataSubsystemError, self.handle_data_error)
        app.register_error_handler(404, self.handle_unknown_url)
 
    def handle_data_error(self, error):
        current_app.logger.warning("%s: %s", type(error).__name__, error.message)
        return jsonify(error.to_dict()), error.status_code
 
    def handle_unknown_url(self, error):
        body = {"error": "NotFound", "message": "this URL doesn't exist", "details": {}}
        return jsonify(body), 404
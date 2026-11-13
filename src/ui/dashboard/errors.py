"""Dashboard-specific exception handling for the Streamlit UI."""

import logging
import sqlite3
from collections.abc import Callable
from typing import Any


logger = logging.getLogger(__name__)


class DashboardOperationError(RuntimeError):
    """A safe, user-facing failure raised by a dashboard operation."""


class DashboardErrorHandler:
    """Translate data/service failures into dashboard-friendly exceptions."""

    @staticmethod
    def message(error: Exception, operation: str) -> str:
        """Return a useful message without exposing unexpected internals."""
        if isinstance(error, ValueError):
            return f"Invalid data while {operation}: {error}"
        if isinstance(error, (sqlite3.Error, OSError)):
            return (
                f"Could not complete {operation} because dashboard data "
                "is unavailable."
            )
        return f"Unexpected error while {operation}. Please try again."

    @classmethod
    def execute(
        cls,
        operation: str,
        callback: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Run one service operation and normalize failures for the UI."""
        try:
            return callback(*args, **kwargs)
        except Exception as error:
            logger.exception("Dashboard operation failed: %s", operation)
            raise DashboardOperationError(
                cls.message(error, operation)
            ) from error
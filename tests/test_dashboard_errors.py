"""Tests for dashboard exception handling and UI components."""

import sqlite3
from unittest.mock import MagicMock, patch

import pytest

from ui.dashboard.components import DashboardHeader, MetricCard
from ui.dashboard.errors import DashboardErrorHandler, DashboardOperationError


def raise_error(error):
    raise error


def test_execute_returns_callback_result():
    assert DashboardErrorHandler.execute("load data", lambda: 42) == 42


def test_execute_passes_positional_arguments():
    assert DashboardErrorHandler.execute(
        "add values", lambda a, b: a + b, 2, 3
    ) == 5


def test_execute_passes_keyword_arguments():
    callback = lambda *, value: value
    assert DashboardErrorHandler.execute(
        "read value", callback, value="ok"
    ) == "ok"


def test_value_error_becomes_dashboard_error_with_input_detail():
    with pytest.raises(DashboardOperationError, match="Invalid data.*bad date"):
        DashboardErrorHandler.execute(
            "load readings", raise_error, ValueError("bad date")
        )


def test_sqlite_error_becomes_safe_dashboard_message():
    with pytest.raises(DashboardOperationError, match="data is unavailable"):
        DashboardErrorHandler.execute(
            "load buildings",
            raise_error,
            sqlite3.OperationalError("secret db path"),
        )


def test_os_error_becomes_safe_dashboard_message():
    with pytest.raises(DashboardOperationError, match="data is unavailable"):
        DashboardErrorHandler.execute(
            "read report", raise_error, OSError("disk detail")
        )


def test_unexpected_error_does_not_expose_internal_details():
    with pytest.raises(DashboardOperationError) as caught:
        DashboardErrorHandler.execute(
            "build chart", raise_error, RuntimeError("secret")
        )

    assert "secret" not in str(caught.value)
    assert "Please try again" in str(caught.value)


def test_normalized_error_preserves_original_cause():
    original = ValueError("bad input")

    with pytest.raises(DashboardOperationError) as caught:
        DashboardErrorHandler.execute("load data", raise_error, original)

    assert caught.value.__cause__ is original


def test_error_message_includes_operation_name():
    message = DashboardErrorHandler.message(
        ValueError("invalid"), "calculate emissions"
    )
    assert "calculate emissions" in message


def test_message_distinguishes_invalid_input():
    assert DashboardErrorHandler.message(
        ValueError("invalid range"), "query"
    ) == "Invalid data while query: invalid range"


def test_header_rejects_empty_title():
    with pytest.raises(ValueError, match="title"):
        DashboardHeader("  ", "Subtitle")


def test_header_rejects_empty_subtitle():
    with pytest.raises(ValueError, match="subtitle"):
        DashboardHeader("Overview", "  ")


def test_header_strips_text_and_renders():
    header = DashboardHeader(" Overview ", " Energy insights ")

    with patch("ui.dashboard.components.st") as streamlit:
        header.initialize()

    assert header.title == "Overview"
    assert header.subtitle == "Energy insights"
    streamlit.title.assert_called_once_with("Overview", anchor=False)
    streamlit.caption.assert_called_once_with("Energy insights")


def test_metric_card_rejects_empty_label():
    with pytest.raises(ValueError, match="label"):
        MetricCard(" ", "10", "energy")


def test_metric_card_rejects_none_value():
    with pytest.raises(ValueError, match="value"):
        MetricCard("Energy", None, "energy")


def test_metric_card_rejects_empty_key():
    with pytest.raises(ValueError, match="key"):
        MetricCard("Energy", "10", " ")


def test_metric_card_rejects_non_string_icon():
    with pytest.raises(ValueError, match="icon"):
        MetricCard("Energy", "10", "energy", icon=12)


def test_metric_card_rejects_non_string_delta():
    with pytest.raises(ValueError, match="delta"):
        MetricCard("Energy", "10", "energy", delta=12)


def test_metric_card_renders_metric_in_container():
    card = MetricCard(
        "Energy", "10 kWh", "energy", icon="bolt", delta="+2%"
    )

    with patch("ui.dashboard.components.st") as streamlit:
        streamlit.container.return_value.__enter__ = MagicMock()
        streamlit.container.return_value.__exit__ = MagicMock(
            return_value=False
        )
        card.initialize()

    streamlit.container.assert_called_once_with(
        border=True, key="energy"
    )
    streamlit.metric.assert_called_once_with(
        "Energy",
        "10 kWh",
        delta="+2%",
        delta_color="normal",
        icon="bolt",
    )
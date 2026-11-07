"""Two repository tests verify query binding and cleanup on failures."""

from datetime import date
from unittest.mock import MagicMock

import pymysql
import pytest

from hometask_assignments.hometask4.subsystem3_advisor.errors import AdvisorDatabaseError
from hometask_assignments.hometask4.subsystem3_advisor.repository import EnergyRepository


def test_summary_query_binds_id_and_closes_connection(monkeypatch):
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.fetchall.return_value = [{'building_id': 7, 'report_date': date(2016, 12, 1)}]
    monkeypatch.setattr(pymysql, 'connect', lambda **settings: connection)

    result = EnergyRepository({}).get_summary(7)

    sql, params = cursor.execute.call_args.args
    assert 'WHERE building_id = %s' in sql
    assert params == (7,)
    assert result['report_date'] == '2016-12-01'
    connection.close.assert_called_once()


def test_query_failure_preserves_cause_and_closes_connection(monkeypatch):
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    original = pymysql.ProgrammingError(1146, 'private table details')
    cursor.execute.side_effect = original
    monkeypatch.setattr(pymysql, 'connect', lambda **settings: connection)

    with pytest.raises(AdvisorDatabaseError) as caught:
        EnergyRepository({}).list_summaries()

    assert caught.value.__cause__ is original
    assert 'private' not in str(caught.value)
    connection.close.assert_called_once()

"""Thirteen application tests for output, advice rules, and failure responses."""

import pymysql

from hometask_assignments.hometask4.subsystem3_advisor.app import create_app
from hometask_assignments.hometask4.subsystem3_advisor.repository import EnergyRepository


def test_homepage_displays_energy_summaries(client):
    response = client.get('/')
    assert response.status_code == 200
    assert 'Demo Home' in response.text and 'Demo Office' in response.text
    assert '57.60' in response.text and '/api/advice/2' in response.text


def test_summaries_endpoint_returns_stored_values(client):
    response = client.get('/api/summaries')
    assert response.status_code == 200
    assert len(response.json) == 2
    assert response.json[1]['energy_kwh'] == 192.0
    assert response.json[1]['co2_kg'] == 72.96


def test_after_hours_advice_uses_the_building_summary(client):
    response = client.get('/api/advice/2')
    assert response.status_code == 200
    assert response.json['after_hours_kwh'] == 48.0
    assert 'equipment schedules' in response.json['advice']


def test_zero_after_hours_use_gets_comparison_advice(client):
    response = client.get('/api/advice/1')
    assert response.status_code == 200
    assert 'previous periods' in response.json['advice']


def test_missing_building_returns_json_404(client):
    response = client.get('/api/advice/99999')
    assert response.status_code == 404
    assert response.json['error'] == 'SummaryNotFoundError'


def test_unknown_route_returns_json_404(client):
    response = client.get('/unknown')
    assert response.status_code == 404
    assert response.json['error'] == 'Not Found'


def test_unsupported_method_returns_json_405(client):
    response = client.post('/api/summaries', json={})
    assert response.status_code == 405
    assert response.json['error'] == 'Method Not Allowed'


def test_database_connection_failure_returns_safe_503(monkeypatch):
    def unavailable(**settings):
        raise pymysql.OperationalError(2003, 'private database credentials')
    monkeypatch.setattr(pymysql, 'connect', unavailable)
    client = create_app(EnergyRepository({})).test_client()
    response = client.get('/api/summaries')
    assert response.status_code == 503
    assert response.json['error'] == 'AdvisorDatabaseError'
    assert 'private' not in response.text


def test_unexpected_failure_returns_safe_500(client, repository, monkeypatch):
    def broken():
        raise RuntimeError('private server details')
    monkeypatch.setattr(repository, 'list_summaries', broken)
    response = client.get('/api/summaries')
    assert response.status_code == 500
    assert response.json['error'] == 'InternalError'
    assert 'private' not in response.text


def test_invalid_energy_values_are_rejected(client, repository):
    for value in (-1, 'high', True):
        repository.rows[0]['energy_kwh'] = value
        response = client.get('/api/advice/1')
        assert response.status_code == 422
        assert response.json['error'] == 'InvalidSummaryError'
        assert 'energy_kwh' in response.json['message']


def test_nonfinite_emissions_are_rejected(client, repository):
    for value in (float('nan'), float('inf')):
        repository.rows[0]['co2_kg'] = value
        response = client.get('/api/advice/1')
        assert response.status_code == 422
        assert 'co2_kg' in response.json['message']


def test_after_hours_energy_cannot_exceed_total(client, repository):
    repository.rows[0]['after_hours_kwh'] = 49
    response = client.get('/api/advice/1')
    assert response.status_code == 422
    assert 'cannot exceed' in response.json['message']


def test_missing_summary_metric_is_rejected(client, repository):
    del repository.rows[0]['cost_eur']
    response = client.get('/api/advice/1')
    assert response.status_code == 422
    assert 'cost_eur' in response.json['message']

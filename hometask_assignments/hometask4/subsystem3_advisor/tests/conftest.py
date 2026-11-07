"""Fresh summary fixtures; the unit/component suite does not need MySQL."""

from copy import deepcopy

import pytest

from hometask_assignments.hometask4.subsystem3_advisor.app import create_app


class MemoryRepository:
    def __init__(self):
        self.rows = [
            {'building_id': 1, 'building': 'Demo Home', 'report_date': '2016-12-01',
             'energy_kwh': 48.0, 'cost_eur': 14.4, 'co2_kg': 18.24, 'after_hours_kwh': 0.0},
            {'building_id': 2, 'building': 'Demo Office', 'report_date': '2016-12-01',
             'energy_kwh': 192.0, 'cost_eur': 57.6, 'co2_kg': 72.96, 'after_hours_kwh': 48.0},
        ]

    def list_summaries(self):
        return deepcopy(self.rows)

    def get_summary(self, building_id):
        return next((deepcopy(row) for row in self.rows if row['building_id'] == building_id), None)


@pytest.fixture
def repository():
    return MemoryRepository()


@pytest.fixture
def client(repository):
    app = create_app(repository)
    app.config['TESTING'] = True
    return app.test_client()

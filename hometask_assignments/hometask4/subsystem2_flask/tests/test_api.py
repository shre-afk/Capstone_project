"""Tests 9-15: the whole app through the Flask test client."""
 
from app import create_app
from errors import DatabaseUnavailableError
 
 
def test_list_buildings_returns_all_six(client):
    response = client.get("/api/buildings")
    assert response.status_code == 200
    assert len(response.get_json()) == 6
 
 
def test_unknown_building_gives_clean_404(client):
    response = client.get("/api/buildings/999/kpis")
    assert response.status_code == 404
    assert response.get_json()["error"] == "NotFoundError"
 
 
def test_kpis_add_up_correctly(client):
    body = client.get("/api/buildings/4/kpis").get_json()
    assert body["readings"] == 2
    assert body["energy_kwh"] == 26.6                 # 12.5 + 14.1
    assert body["cost_eur"] == round(26.6 * 0.30, 2)
    assert body["co2_kg"] == round(26.6 * 0.38, 1)
 
 
def test_kpis_with_backwards_period_give_400(client):
    url = "/api/buildings/4/kpis?start=2016-12-02 00:00:00&end=2016-12-01 00:00:00"
    response = client.get(url)
    assert response.status_code == 400
    assert response.get_json()["error"] == "ValidationError"
 
 
def test_post_valid_reading_is_stored(client):
    new = {"meter_id": 6, "ts_utc": "2016-12-01 07:15:00", "value": 2.9}
    assert client.post("/api/readings", json=new).status_code == 201
    stored = client.get("/api/buildings/6/readings").get_json()
    assert len(stored) == 2
 
 
def test_post_same_meter_and_time_twice_gives_409(client):
    duplicate = {"meter_id": 1, "ts_utc": "2016-12-01 07:00:00", "value": 0.4}
    response = client.post("/api/readings", json=duplicate)
    assert response.status_code == 409
    assert response.get_json()["error"] == "DuplicateReadingError"
 
 
class BrokenRepository:
    """Pretends MySQL is down: the one method we call blows up."""
 
    def list_buildings(self):
        raise DatabaseUnavailableError("can't reach MySQL, is the server running?")
 
 
def test_database_down_gives_503_instead_of_crash():
    client = create_app(BrokenRepository()).test_client()
    response = client.get("/api/buildings")
    assert response.status_code == 503
    assert response.get_json()["error"] == "DatabaseUnavailableError"
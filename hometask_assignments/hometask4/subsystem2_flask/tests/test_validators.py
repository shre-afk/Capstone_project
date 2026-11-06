"""Tests 4-8: the input checks, without Flask involved at all."""
 
import pytest
 
from errors import ValidationError
from validators import check_plausible, parse_period, parse_reading
 
GOOD = {"meter_id": 1, "ts_utc": "2016-12-01 08:00:00", "value": 0.5}
 
 
def test_good_data_passes_and_gets_converted():
    assert parse_reading({"meter_id": "1", "ts_utc": GOOD["ts_utc"], "value": "0.5"}) == (1, GOOD["ts_utc"], 0.5)
 
 
def test_missing_field_is_reported_by_name():
    with pytest.raises(ValidationError) as caught:
        parse_reading({"meter_id": 1, "value": 0.5})
    assert caught.value.details == {"missing": ["ts_utc"]}
 
 
def test_badly_written_timestamp_is_rejected():
    with pytest.raises(ValidationError):
        parse_reading({**GOOD, "ts_utc": "yesterday at 9"})
 
 
def test_limit_depends_on_building_type():
    check_plausible(9.9, "business")             # fine for an office, no error
    with pytest.raises(ValidationError):
        check_plausible(9.9, "home")             # impossible for a home (limit 5 kWh)
 
 
def test_period_must_start_before_it_ends():
    with pytest.raises(ValidationError):
        parse_period("2016-12-02 00:00:00", "2016-12-01 00:00:00")
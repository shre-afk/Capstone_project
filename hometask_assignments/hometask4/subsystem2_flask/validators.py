"""Checks incoming data BEFORE it gets anywhere near the database"""
 
from datetime import datetime
 
from errors import ValidationError
 
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"                                   # e.g. 2016-12-01 07:15:00
MAX_KWH_PER_INTERVAL = {"home": 5.0, "business": 100.0, "public": 50.0}   # as in config.toml
 
 
def _parse_time(text, field):
    try:
        return datetime.strptime(text, TIME_FORMAT)
    except (TypeError, ValueError):
        raise ValidationError(f"{field} must look like 2016-12-01 07:15:00", {field: text})
 
 
def parse_reading(data):
    """JSON of a POST request -> (meter_id, ts_utc, value), or ValidationError."""
    if not isinstance(data, dict):
        raise ValidationError("send a JSON object like {\"meter_id\": 1, ...}")
 
    missing = [field for field in ("meter_id", "ts_utc", "value") if field not in data]
    if missing:
        raise ValidationError("some fields are missing", {"missing": missing})
 
    try:
        meter_id = int(data["meter_id"])
        value = float(data["value"])
    except (TypeError, ValueError):
        raise ValidationError("meter_id and value have to be numbers")
 
    _parse_time(data["ts_utc"], "ts_utc")
    return meter_id, data["ts_utc"], value
 
 
def check_plausible(value, building_type):
    """capstone's validation rule: 0 <= kWh <= limit for this building type"""
    limit = MAX_KWH_PER_INTERVAL[building_type]
    if not 0 <= value <= limit:
        raise ValidationError(f"{value} kWh in 15 min is impossible for a {building_type} "
                              f"(allowed 0 to {limit})", {"value": value, "limit": limit})
 
 
def parse_period(start, end):
    """Two time texts -> checked; start must be before end (end excluded)"""
    if _parse_time(start, "start") >= _parse_time(end, "end"):
        raise ValidationError("start must be before end", {"start": start, "end": end})
    return start, end
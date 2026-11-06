"""Tests 1-3: the error classes themselves."""
 
import pytest
 
from errors import (DatabaseUnavailableError, DataSubsystemError, DuplicateReadingError,
                    NotFoundError, ValidationError)
 
 
def test_all_errors_share_one_parent():
    with pytest.raises(DataSubsystemError):
        raise DuplicateReadingError("boom")
 
 
def test_every_error_has_the_right_status_code():
    assert ValidationError("x").status_code == 400
    assert NotFoundError("x").status_code == 404
    assert DuplicateReadingError("x").status_code == 409
    assert DatabaseUnavailableError("x").status_code == 503
 
 
def test_to_dict_gives_name_message_and_details():
    error = ValidationError("kwh can't be negative", {"kwh": -1})
    assert error.to_dict() == {
        "error": "ValidationError",
        "message": "kwh can't be negative",
        "details": {"kwh": -1},
    }
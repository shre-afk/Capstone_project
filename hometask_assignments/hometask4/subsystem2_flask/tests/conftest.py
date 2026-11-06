"""Fixtures = things pytest builds fresh for every test that asks for them by name."""
 
import pytest
 
from app import create_app
from repository import InMemoryRepository
 
 
@pytest.fixture
def repo():
    return InMemoryRepository.with_sample_data()     # brand-new data for every test
 
 
@pytest.fixture
def client(repo):
    app = create_app(repo)
    app.config["TESTING"] = True
    return app.test_client()                         # a fake browser, no server needed
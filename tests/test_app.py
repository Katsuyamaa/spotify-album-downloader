import pytest
from app import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c

def test_index_returns_200(client):
    response = client.get("/")
    assert response.status_code == 200

def test_index_contains_form(client):
    response = client.get("/")
    assert b"form" in response.data
    assert b"url" in response.data

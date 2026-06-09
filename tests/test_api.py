import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestAuth:
    def test_register(self, client):
        response = client.post("/auth/register", json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpass123"
        })
        assert response.status_code in [201, 400]  # 400 si déjà existant
    
    def test_login_invalid(self, client):
        response = client.post("/auth/login", json={
            "email": "invalid@example.com",
            "password": "wrongpass"
        })
        assert response.status_code == 401


class TestHealth:
    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
    
    def test_root(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "SentiFlow" in response.json()["message"]

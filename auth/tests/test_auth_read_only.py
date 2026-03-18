from fastapi.testclient import TestClient
from app.main import app
from app.routes import auth_routes


client = TestClient(app)


def test_get_me_success(monkeypatch):
    monkeypatch.setattr(
        auth_routes,
        "verify_token",
        lambda token: {"user_id": "u-1", "email": "user@example.com"},
    )
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"


def test_get_me_invalid_token(monkeypatch):
    monkeypatch.setattr(auth_routes, "verify_token", lambda token: None)
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"


def test_login_success(monkeypatch):
    monkeypatch.setattr(auth_routes, "login_user", lambda email, password: "jwt-token")
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "secret"},
    )
    assert response.status_code == 200
    assert response.json()["access_token"] == "jwt-token"


from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models.user import User

REGISTER_PAYLOAD = {
    "name": "Ada Lovelace",
    "email": "ada@example.com",
    "password": "correct-horse-battery-staple",
    "role": "student",
}


def register(client: TestClient) -> dict[str, object]:
    response = client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    assert response.status_code == 201
    return response.json()


def test_successful_registration(client: TestClient, db_session: Session) -> None:
    body = register(client)

    assert body["name"] == "Ada Lovelace"
    assert body["email"] == "ada@example.com"
    assert body["role"] == "student"
    assert "password" not in body
    assert "password_hash" not in body

    user = db_session.scalar(select(User).where(User.email == "ada@example.com"))
    assert user is not None
    assert user.password_hash != REGISTER_PAYLOAD["password"]
    assert verify_password(REGISTER_PAYLOAD["password"], user.password_hash)


def test_duplicate_email_rejected_case_insensitively(client: TestClient) -> None:
    register(client)
    duplicate = {**REGISTER_PAYLOAD, "email": "ADA@example.com"}

    response = client.post("/api/v1/auth/register", json=duplicate)

    assert response.status_code == 409


def test_successful_login(client: TestClient) -> None:
    register(client)

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "ada@example.com", "password": REGISTER_PAYLOAD["password"]},
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_incorrect_password_rejected(client: TestClient) -> None:
    register(client)

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "ada@example.com", "password": "definitely-wrong"},
    )

    assert response.status_code == 401


def test_authenticated_users_me(client: TestClient) -> None:
    registered = register(client)
    login = client.post(
        "/api/v1/auth/login",
        data={"username": "ada@example.com", "password": REGISTER_PAYLOAD["password"]},
    )

    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )

    assert response.status_code == 200
    assert response.json() == registered


def test_unauthenticated_users_me(client: TestClient) -> None:
    response = client.get("/api/v1/users/me")

    assert response.status_code == 401


def test_invalid_role_and_malformed_input_rejected(client: TestClient) -> None:
    invalid = {
        **REGISTER_PAYLOAD,
        "email": "not-an-email",
        "password": "short",
        "role": "admin",
    }

    response = client.post("/api/v1/auth/register", json=invalid)

    assert response.status_code == 422
    error_fields = {error["loc"][-1] for error in response.json()["detail"]}
    assert {"email", "password", "role"}.issubset(error_fields)


def test_malformed_token_rejected(client: TestClient) -> None:
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer not-a-jwt"},
    )

    assert response.status_code == 401


def test_login_openapi_uses_oauth2_form(client: TestClient) -> None:
    operation = client.get("/openapi.json").json()["paths"]["/api/v1/auth/login"]["post"]

    assert "application/x-www-form-urlencoded" in operation["requestBody"]["content"]

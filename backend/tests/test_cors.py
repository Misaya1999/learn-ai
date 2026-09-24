from fastapi.testclient import TestClient


PREFLIGHT_HEADERS = {
    "Access-Control-Request-Method": "POST",
    "Access-Control-Request-Headers": "content-type",
}


def test_preflight_accepts_configured_origin_without_trailing_slash(
    client: TestClient,
) -> None:
    origin = "http://localhost:3000"

    response = client.options(
        "/api/v1/auth/register",
        headers={"Origin": origin, **PREFLIGHT_HEADERS},
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin


def test_preflight_does_not_grant_unconfigured_origin(client: TestClient) -> None:
    response = client.options(
        "/api/v1/auth/register",
        headers={"Origin": "https://not-allowed.example", **PREFLIGHT_HEADERS},
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers

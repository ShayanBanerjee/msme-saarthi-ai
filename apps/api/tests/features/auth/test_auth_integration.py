"""Persistent encrypted identity and secure-session integration tests."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_register_authenticate_logout_and_login(client: TestClient) -> None:
    registration = client.post(
        "/api/v1/auth/register",
        headers={"Origin": "http://127.0.0.1:5173"},
        json={
            "email": "founder@example.test",
            "password": "Correct-Horse-Foundry-2026",
            "full_name": "Asha Mehta",
            "business_name": "Asha Circular Works",
        },
    )

    assert registration.status_code == 201
    assert registration.json()["email"] == "founder@example.test"
    assert registration.json()["business_name"] == "Asha Circular Works"
    cookie = registration.headers["set-cookie"]
    assert "HttpOnly" in cookie
    assert "SameSite=strict" in cookie
    assert "founder@example.test" not in cookie

    current = client.get("/api/v1/auth/me")
    assert current.status_code == 200
    assert current.json()["full_name"] == "Asha Mehta"

    logout = client.post(
        "/api/v1/auth/logout", headers={"Origin": "http://127.0.0.1:5173"}
    )
    assert logout.status_code == 204
    assert client.get("/api/v1/auth/me").status_code == 401

    login = client.post(
        "/api/v1/auth/login",
        headers={"Origin": "http://127.0.0.1:5173"},
        json={
            "email": "founder@example.test",
            "password": "Correct-Horse-Foundry-2026",
        },
    )
    assert login.status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 200


@pytest.mark.integration
def test_duplicate_invalid_credentials_and_untrusted_origin_are_rejected(
    client: TestClient,
) -> None:
    payload = {
        "email": "owner@example.test",
        "password": "Long-Unique-Password-2026",
        "full_name": "Neel Shah",
        "business_name": "Neel Precision Labs",
    }
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    assert client.post("/api/v1/auth/register", json=payload).status_code == 409

    client.post("/api/v1/auth/logout")
    invalid = client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": "wrong"},
    )
    assert invalid.status_code == 401
    assert invalid.json()["code"] == "invalid_credentials"

    blocked = client.post(
        "/api/v1/auth/login",
        headers={"Origin": "https://attacker.example"},
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert blocked.status_code == 403


def test_registration_validation_rejects_weak_or_unknown_input(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "not-an-email",
            "password": "short",
            "full_name": " ",
            "business_name": "Example",
            "role": "admin",
        },
    )
    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"

"""Tests for authentication and registration endpoints."""
from fastapi.testclient import TestClient


def test_register_patient(client: TestClient):
    """Test patient registration creates user, returns token, and sets role."""
    payload = {
        "email": "testpatient@example.com",
        "password": "SecurePassword123!",
        "full_name": "Jane Patient",
        "phone_number": "+1234567890",
        "role": "PATIENT",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "PATIENT"
    assert data["email"] == "testpatient@example.com"


def test_login_success(client: TestClient):
    """Test user login with valid credentials."""
    # First register
    register_payload = {
        "email": "doctorlogin@example.com",
        "password": "DoctorPassword123!",
        "full_name": "Dr. John Doe",
        "role": "DOCTOR",
    }
    client.post("/api/v1/auth/register", json=register_payload)

    # Now login
    login_payload = {
        "email": "doctorlogin@example.com",
        "password": "DoctorPassword123!",
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "DOCTOR"


def test_login_invalid_password(client: TestClient):
    """Test login with incorrect password returns 401."""
    login_payload = {
        "email": "nonexistent@example.com",
        "password": "WrongPassword!",
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401

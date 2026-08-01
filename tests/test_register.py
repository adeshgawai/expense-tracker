import pytest
from app import app
from database.db import get_db, get_user_by_email


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client


def test_register_page_get(client):
    """GET /register should return HTTP 200 and display registration form."""
    response = client.get("/register")
    assert response.status_code == 200
    assert b"Create your account" in response.data
    assert b'name="name"' in response.data
    assert b'name="email"' in response.data
    assert b'name="password"' in response.data


def test_register_success(client):
    """POST /register with valid inputs should create user, set session, and redirect to profile."""
    test_email = "newuser.test@example.com"

    response = client.post(
        "/register",
        data={
            "name": "New Test User",
            "email": test_email,
            "password": "securepassword123",
        },
        follow_redirects=False,
    )

    # Should redirect to profile page
    assert response.status_code == 302
    assert response.headers["Location"] in ["/profile", "http://localhost/profile"]

    # Verify user exists in DB
    user = get_user_by_email(test_email)
    assert user is not None
    assert user["name"] == "New Test User"
    assert user["email"] == test_email
    assert user["password_hash"] != "securepassword123"

    # Verify session set
    with client.session_transaction() as sess:
        assert sess.get("user_id") == user["id"]
        assert sess.get("user_name") == "New Test User"


def test_register_duplicate_email(client):
    """POST /register with an existing email should fail with error message."""
    response = client.post(
        "/register",
        data={
            "name": "Duplicate User",
            "email": "demo@spendly.com",  # Already exists in DB seed
            "password": "anotherpassword123",
        },
    )

    assert response.status_code == 200
    assert b"An account with this email address already exists." in response.data


def test_register_short_password(client):
    """POST /register with password under 8 characters should fail with error message."""
    response = client.post(
        "/register",
        data={
            "name": "Short Pass User",
            "email": "shortpass@example.com",
            "password": "short",
        },
    )

    assert response.status_code == 200
    assert b"Password must be at least 8 characters long." in response.data


def test_register_missing_fields(client):
    """POST /register with missing required fields should fail with error message."""
    response = client.post(
        "/register",
        data={
            "name": "",
            "email": "missing@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 200
    assert b"All fields are required." in response.data


def test_register_retains_form_values_on_error(client):
    """POST /register validation failure should re-render entered name and email values."""
    response = client.post(
        "/register",
        data={
            "name": "Retain Name Test",
            "email": "retain@example.com",
            "password": "123",  # triggers short password error
        },
    )

    assert response.status_code == 200
    assert b'value="Retain Name Test"' in response.data
    assert b'value="retain@example.com"' in response.data

import pytest
from app import app
from database.db import get_user_by_email


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client


def test_login_page_get_unauthenticated(client):
    """GET /login when not logged in should return HTTP 200 and render login form."""
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Welcome back" in response.data
    assert b'name="email"' in response.data
    assert b'name="password"' in response.data


def test_login_page_get_authenticated_redirects(client):
    """GET /login when user is logged in should redirect to profile page."""
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_name"] = "Demo User"

    response = client.get("/login", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"] in ["/profile", "http://localhost/profile"]


def test_login_missing_fields(client):
    """POST /login with missing email or password should return error."""
    response = client.post(
        "/login",
        data={
            "email": "",
            "password": "",
        },
    )
    assert response.status_code == 200
    assert b"All fields are required." in response.data


def test_login_nonexistent_email(client):
    """POST /login with unregistered email address should return invalid credentials error."""
    response = client.post(
        "/login",
        data={
            "email": "notregistered@example.com",
            "password": "somepassword123",
        },
    )
    assert response.status_code == 200
    assert b"Invalid email or password." in response.data


def test_login_incorrect_password(client):
    """POST /login with wrong password for existing user should return invalid credentials error."""
    response = client.post(
        "/login",
        data={
            "email": "demo@spendly.com",
            "password": "wrongpassword123",
        },
    )
    assert response.status_code == 200
    assert b"Invalid email or password." in response.data


def test_login_success(client):
    """POST /login with correct email and password should authenticate user and redirect to profile page."""
    response = client.post(
        "/login",
        data={
            "email": "demo@spendly.com",
            "password": "demo123",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["Location"] in ["/profile", "http://localhost/profile"]

    with client.session_transaction() as sess:
        assert sess.get("user_id") is not None
        assert sess.get("user_name") == "Demo User"


def test_logout_clears_session(client):
    """GET /logout should clear user session and redirect to home page."""
    # First, authenticate
    client.post(
        "/login",
        data={
            "email": "demo@spendly.com",
            "password": "demo123",
        },
    )

    with client.session_transaction() as sess:
        assert sess.get("user_id") is not None

    # Perform logout
    response = client.get("/logout", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"] in ["/", "http://localhost/"]

    with client.session_transaction() as sess:
        assert sess.get("user_id") is None
        assert sess.get("user_name") is None

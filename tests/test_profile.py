import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client


def test_profile_unauthenticated_redirects(client):
    """GET /profile without active session should redirect to /login."""
    response = client.get("/profile", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"] in ["/login", "http://localhost/login"]


def test_profile_authenticated_success(client):
    """GET /profile with valid authenticated user session should render profile page and category breakdown."""
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_name"] = "Demo User"

    response = client.get("/profile")
    assert response.status_code == 200
    assert b"Demo User" in response.data
    assert b"demo@spendly.com" in response.data
    assert b"Total Expenses" in response.data
    assert b"Total Amount Spent" in response.data
    assert b"Spending by Category" in response.data
    assert b"Food" in response.data


def test_profile_invalid_user_session(client):
    """GET /profile with non-existent user_id in session should clear session and redirect to login."""
    with client.session_transaction() as sess:
        sess["user_id"] = 99999
        sess["user_name"] = "Ghost User"

    response = client.get("/profile", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"] in ["/login", "http://localhost/login"]

    with client.session_transaction() as sess:
        assert sess.get("user_id") is None

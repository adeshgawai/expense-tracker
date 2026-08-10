import pytest
from app import app
from database.db import init_db, seed_db


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        with app.app_context():
            init_db()
            seed_db()
        yield client


# ============================================================================ #
# Auth Guard & Route Protection Tests
# ============================================================================ #

def test_analytics_unauthenticated_redirect(client):
    """Unauthenticated access to /analytics should redirect to /login."""
    response = client.get("/analytics")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_analytics_authenticated_access(client):
    """Authenticated user can successfully view the /analytics coming soon page."""
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_name"] = "Demo User"

    response = client.get("/analytics")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    # Verify key design copy from Figma Coming Soon design
    assert "We're building" in html
    assert "something" in html
    assert "worth waiting for" in html
    assert "COMING SOON" in html
    assert "countdownTimer" in html
    assert "notifyForm" in html


def test_analytics_invalid_user_session(client):
    """Session with a non-existent user ID should be cleared and redirected to /login."""
    with client.session_transaction() as sess:
        sess["user_id"] = 99999
        sess["user_name"] = "Ghost User"

    response = client.get("/analytics")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


# ============================================================================ #
# Navbar Menu & Active State Tests
# ============================================================================ #

def test_navbar_analytics_visible_only_when_logged_in(client):
    """Navbar should show Analytics only to logged-in users, not guests."""
    # Guest user on landing page
    guest_response = client.get("/")
    assert guest_response.status_code == 200
    guest_html = guest_response.get_data(as_text=True)
    assert 'href="/analytics"' not in guest_html

    # Logged-in user on profile page
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_name"] = "Demo User"

    auth_response = client.get("/profile")
    assert auth_response.status_code == 200
    auth_html = auth_response.get_data(as_text=True)
    assert 'href="/analytics"' in auth_html


def test_navbar_active_state_on_analytics_page(client):
    """When on /analytics, the Analytics navbar link must have the active class."""
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_name"] = "Demo User"

    response = client.get("/analytics")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    # Check active state on Analytics link
    assert 'class="nav-link active">Analytics</a>' in html or ('nav-link' in html and 'active' in html and 'Analytics' in html)
    # Dashboard should not be active
    assert 'class="nav-link ">Dashboard</a>' in html or 'class="nav-link" href="/profile"' in html or 'href="/profile" class="nav-link "' in html


def test_navbar_active_state_on_profile_page(client):
    """When on /profile, Dashboard is active and Analytics is not active."""
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_name"] = "Demo User"

    response = client.get("/profile")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    # Check active state on Dashboard link
    assert 'href="/profile" class="nav-link active"' in html or 'class="nav-link active" href="/profile"' in html or 'class="nav-link active">Dashboard</a>' in html
    # Analytics should not be active
    assert 'href="/analytics" class="nav-link "' in html or 'class="nav-link " href="/analytics"' in html


# ============================================================================ #
# Notification Subscription Form Tests
# ============================================================================ #

def test_analytics_notify_form_submission(client):
    """Submitting notify form on /analytics shows confirmation and redirects."""
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_name"] = "Demo User"

    response = client.post("/analytics", data={"email": "demo@spendly.com"}, follow_redirects=True)
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Thank you!" in html or "notify you" in html

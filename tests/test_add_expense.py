import pytest
from datetime import datetime
from app import app
from database.db import create_expense, create_user, get_db, get_user_by_email, init_db, seed_db


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        with app.app_context():
            init_db()
            seed_db()
        yield client


@pytest.fixture
def test_user():
    """Provides an isolated test user and cleans up created test data after test completion."""
    with app.app_context():
        email = "add_expense_test_user@spendly.com"
        user = get_user_by_email(email)
        if user:
            user_id = user["id"]
        else:
            user_id = create_user("Add Expense Tester", email, "password123")

    yield {"id": user_id, "name": "Add Expense Tester", "email": email}

    # Cleanup any expenses created by this test user
    with app.app_context():
        conn = get_db()
        conn.execute("DELETE FROM expenses WHERE user_id = ?;", (user_id,))
        conn.execute("DELETE FROM users WHERE id = ?;", (user_id,))
        conn.commit()
        conn.close()


# ============================================================================ #
# Database Function Unit Tests
# ============================================================================ #

def test_db_create_expense(test_user):
    """create_expense should insert an expense record and return its new ID."""
    with app.app_context():
        expense_id = create_expense(
            user_id=test_user["id"],
            amount=99.50,
            category="Food",
            date="2026-08-10",
            description="Team lunch",
        )
        assert expense_id is not None
        assert expense_id > 0

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM expenses WHERE id = ?;", (expense_id,))
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row["user_id"] == test_user["id"]
        assert row["amount"] == 99.50
        assert row["category"] == "Food"
        assert row["date"] == "2026-08-10"
        assert row["description"] == "Team lunch"


# ============================================================================ #
# Route Auth Guard Tests
# ============================================================================ #

def test_add_expense_unauthenticated_get_redirects(client):
    """Unauthenticated GET /expenses/add redirects to /login with flash message."""
    response = client.get("/expenses/add", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

    # Following redirect should show warning flash
    redirect_response = client.get("/expenses/add", follow_redirects=True)
    html = redirect_response.get_data(as_text=True)
    assert "Please log in to add an expense" in html


def test_add_expense_unauthenticated_post_redirects(client):
    """Unauthenticated POST /expenses/add redirects to /login."""
    response = client.post(
        "/expenses/add",
        data={
            "amount": "150.00",
            "category": "Food",
            "date": "2026-08-10",
            "description": "Lunch",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


# ============================================================================ #
# Form Rendering & Defaults Tests
# ============================================================================ #

def test_add_expense_authenticated_get_renders_form(client, test_user):
    """Authenticated user sees the Add Expense page with today's date pre-filled."""
    with client.session_transaction() as sess:
        sess["user_id"] = test_user["id"]
        sess["user_name"] = test_user["name"]

    response = client.get("/expenses/add")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    today_str = datetime.now().strftime("%Y-%m-%d")
    assert "Add New Expense" in html
    assert 'name="amount"' in html
    assert 'name="category"' in html
    assert 'name="date"' in html
    assert 'name="description"' in html
    assert f'value="{today_str}"' in html
    assert "Food" in html
    assert "Transport" in html
    assert "Bills" in html


# ============================================================================ #
# Valid Submission Tests
# ============================================================================ #

def test_add_expense_post_valid_creates_expense_and_redirects(client, test_user):
    """Submitting a valid expense persists the record and redirects to /profile with flash."""
    with client.session_transaction() as sess:
        sess["user_id"] = test_user["id"]
        sess["user_name"] = test_user["name"]

    response = client.post(
        "/expenses/add",
        data={
            "amount": "349.99",
            "category": "Shopping",
            "date": "2026-08-10",
            "description": "Ergonomic keyboard",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "Expense added successfully!" in html
    assert "Ergonomic keyboard" in html
    assert "349.99" in html
    assert "Shopping" in html


# ============================================================================ #
# Input Validation Tests
# ============================================================================ #

def test_add_expense_post_missing_fields(client, test_user):
    """Submitting missing amount or category renders validation error and preserves inputs."""
    with client.session_transaction() as sess:
        sess["user_id"] = test_user["id"]
        sess["user_name"] = test_user["name"]

    # Missing amount
    response = client.post(
        "/expenses/add",
        data={
            "amount": "",
            "category": "Food",
            "date": "2026-08-10",
            "description": "Lunch",
        },
    )
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Amount, Category, and Date are required." in html
    assert "Lunch" in html

    # Missing category
    response = client.post(
        "/expenses/add",
        data={
            "amount": "100.00",
            "category": "",
            "date": "2026-08-10",
            "description": "Lunch",
        },
    )
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Amount, Category, and Date are required." in html


def test_add_expense_post_invalid_amount(client, test_user):
    """Submitting non-numeric, zero, or negative amount renders validation error."""
    with client.session_transaction() as sess:
        sess["user_id"] = test_user["id"]
        sess["user_name"] = test_user["name"]

    # Negative amount
    res_neg = client.post(
        "/expenses/add",
        data={
            "amount": "-50.00",
            "category": "Food",
            "date": "2026-08-10",
            "description": "Refund attempt",
        },
    )
    assert res_neg.status_code == 200
    assert "Please enter a valid positive amount." in res_neg.get_data(as_text=True)

    # Zero amount
    res_zero = client.post(
        "/expenses/add",
        data={
            "amount": "0",
            "category": "Food",
            "date": "2026-08-10",
            "description": "Free food",
        },
    )
    assert res_zero.status_code == 200
    assert "Please enter a valid positive amount." in res_zero.get_data(as_text=True)

    # Non-numeric amount
    res_text = client.post(
        "/expenses/add",
        data={
            "amount": "abc",
            "category": "Food",
            "date": "2026-08-10",
            "description": "Invalid",
        },
    )
    assert res_text.status_code == 200
    assert "Please enter a valid positive amount." in res_text.get_data(as_text=True)


def test_add_expense_post_invalid_category(client, test_user):
    """Submitting an unauthorized category returns validation error."""
    with client.session_transaction() as sess:
        sess["user_id"] = test_user["id"]
        sess["user_name"] = test_user["name"]

    response = client.post(
        "/expenses/add",
        data={
            "amount": "50.00",
            "category": "CryptoSpeculation",
            "date": "2026-08-10",
            "description": "Bad trade",
        },
    )
    assert response.status_code == 200
    assert "Please select a valid expense category." in response.get_data(as_text=True)


def test_add_expense_post_invalid_date(client, test_user):
    """Submitting an invalid date string returns validation error."""
    with client.session_transaction() as sess:
        sess["user_id"] = test_user["id"]
        sess["user_name"] = test_user["name"]

    response = client.post(
        "/expenses/add",
        data={
            "amount": "50.00",
            "category": "Food",
            "date": "10-08-2026",  # wrong format (not YYYY-MM-DD)
            "description": "Lunch",
        },
    )
    assert response.status_code == 200
    assert "Please enter a valid date in YYYY-MM-DD format." in response.get_data(as_text=True)


# ============================================================================ #
# Integration: Profile Dashboard Synchronization
# ============================================================================ #

def test_add_expense_updates_profile_stats_and_recent_transactions(client, test_user):
    """Newly created expense updates profile stats, breakdown chart, and recent transactions."""
    with client.session_transaction() as sess:
        sess["user_id"] = test_user["id"]
        sess["user_name"] = test_user["name"]

    # Initial profile state for test user (should have 0 transactions initially)
    init_res = client.get("/profile")
    assert init_res.status_code == 200

    # Post new unique expense
    client.post(
        "/expenses/add",
        data={
            "amount": "555.00",
            "category": "Entertainment",
            "date": "2026-08-10",
            "description": "Concert VIP Ticket",
        },
        follow_redirects=True,
    )

    # Check updated profile
    prof_res = client.get("/profile")
    prof_html = prof_res.get_data(as_text=True)

    assert "Concert VIP Ticket" in prof_html
    assert "555.00" in prof_html
    assert "Entertainment" in prof_html

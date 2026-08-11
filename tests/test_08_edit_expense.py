import pytest
from app import app
from database.db import (
    create_expense,
    create_user,
    get_db,
    get_expense_by_id,
    get_user_by_email,
    init_db,
    seed_db,
    update_expense,
)


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
    """Provides an isolated primary test user and cleans up afterwards."""
    with app.app_context():
        email = "edit_expense_tester1@spendly.com"
        user = get_user_by_email(email)
        if user:
            user_id = user["id"]
        else:
            user_id = create_user("Edit Expense Tester 1", email, "password123")

    yield {"id": user_id, "name": "Edit Expense Tester 1", "email": email}

    with app.app_context():
        conn = get_db()
        conn.execute("DELETE FROM expenses WHERE user_id = ?;", (user_id,))
        conn.execute("DELETE FROM users WHERE id = ?;", (user_id,))
        conn.commit()
        conn.close()


@pytest.fixture
def other_user():
    """Provides a second isolated test user to verify authorization / IDOR barriers."""
    with app.app_context():
        email = "edit_expense_tester2@spendly.com"
        user = get_user_by_email(email)
        if user:
            user_id = user["id"]
        else:
            user_id = create_user("Edit Expense Tester 2", email, "password123")

    yield {"id": user_id, "name": "Edit Expense Tester 2", "email": email}

    with app.app_context():
        conn = get_db()
        conn.execute("DELETE FROM expenses WHERE user_id = ?;", (user_id,))
        conn.execute("DELETE FROM users WHERE id = ?;", (user_id,))
        conn.commit()
        conn.close()


# ============================================================================ #
# Database Layer Function Unit Tests
# ============================================================================ #

def test_db_get_expense_by_id(test_user, other_user):
    """get_expense_by_id retrieves correct record and respects user_id filter."""
    with app.app_context():
        exp_id = create_expense(
            user_id=test_user["id"],
            amount=42.00,
            category="Food",
            date="2026-08-01",
            description="Lunch with colleagues",
        )

        # Retrieve without user_id
        row1 = get_expense_by_id(exp_id)
        assert row1 is not None
        assert row1["id"] == exp_id
        assert row1["amount"] == 42.00
        assert row1["category"] == "Food"

        # Retrieve with matching user_id
        row2 = get_expense_by_id(exp_id, user_id=test_user["id"])
        assert row2 is not None
        assert row2["id"] == exp_id

        # Retrieve with other user_id (should return None)
        row3 = get_expense_by_id(exp_id, user_id=other_user["id"])
        assert row3 is None

        # Non-existent ID
        row4 = get_expense_by_id(999999)
        assert row4 is None


def test_db_update_expense(test_user, other_user):
    """update_expense modifies the record when user_id matches and rejects otherwise."""
    with app.app_context():
        exp_id = create_expense(
            user_id=test_user["id"],
            amount=50.00,
            category="Transport",
            date="2026-08-02",
            description="Train ticket",
        )

        # Attempt update by unauthorized user
        unauth_success = update_expense(
            expense_id=exp_id,
            user_id=other_user["id"],
            amount=999.00,
            category="Bills",
            date="2026-08-03",
            description="Hacked bill",
        )
        assert unauth_success is False

        # Verify record remains unchanged
        unchanged = get_expense_by_id(exp_id)
        assert unchanged["amount"] == 50.00
        assert unchanged["category"] == "Transport"

        # Authorized update
        auth_success = update_expense(
            expense_id=exp_id,
            user_id=test_user["id"],
            amount=75.50,
            category="Bills",
            date="2026-08-05",
            description="Monthly internet",
        )
        assert auth_success is True

        updated = get_expense_by_id(exp_id)
        assert updated["amount"] == 75.50
        assert updated["category"] == "Bills"
        assert updated["date"] == "2026-08-05"
        assert updated["description"] == "Monthly internet"


# ============================================================================ #
# Route Authentication & Authorization Guards
# ============================================================================ #

def test_edit_expense_unauthenticated_get_redirects(client):
    """Unauthenticated GET /expenses/<id>/edit redirects to /login."""
    response = client.get("/expenses/1/edit", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

    followed = client.get("/expenses/1/edit", follow_redirects=True)
    assert "Please log in to edit an expense." in followed.get_data(as_text=True)


def test_edit_expense_unauthenticated_post_redirects(client):
    """Unauthenticated POST /expenses/<id>/edit redirects to /login."""
    response = client.post(
        "/expenses/1/edit",
        data={
            "amount": "100.00",
            "category": "Food",
            "date": "2026-08-01",
            "description": "Lunch",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_edit_expense_nonexistent_or_unauthorized_get(client, test_user, other_user):
    """Accessing non-existent expense or expense owned by another user redirects to /profile."""
    with client.session_transaction() as sess:
        sess["user_id"] = test_user["id"]
        sess["user_name"] = test_user["name"]

    # Non-existent ID
    res_nonexistent = client.get("/expenses/999999/edit", follow_redirects=True)
    assert res_nonexistent.status_code == 200
    assert "Expense not found or unauthorized access." in res_nonexistent.get_data(as_text=True)

    # Expense owned by other_user
    with app.app_context():
        other_exp_id = create_expense(
            user_id=other_user["id"],
            amount=88.00,
            category="Shopping",
            date="2026-08-03",
            description="Other user purchase",
        )

    res_unauth = client.get(f"/expenses/{other_exp_id}/edit", follow_redirects=True)
    assert res_unauth.status_code == 200
    assert "Expense not found or unauthorized access." in res_unauth.get_data(as_text=True)


def test_edit_expense_unauthorized_post_rejected(client, test_user, other_user):
    """Submitting POST to edit another user's expense is rejected without mutating data."""
    with app.app_context():
        other_exp_id = create_expense(
            user_id=other_user["id"],
            amount=88.00,
            category="Shopping",
            date="2026-08-03",
            description="Original item",
        )

    # Log in as test_user
    with client.session_transaction() as sess:
        sess["user_id"] = test_user["id"]
        sess["user_name"] = test_user["name"]

    response = client.post(
        f"/expenses/{other_exp_id}/edit",
        data={
            "amount": "999.00",
            "category": "Health",
            "date": "2026-08-05",
            "description": "Attempted tamper",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Expense not found or unauthorized access." in response.get_data(as_text=True)

    # Verify original item remains unchanged
    with app.app_context():
        exp = get_expense_by_id(other_exp_id)
        assert exp["amount"] == 88.00
        assert exp["description"] == "Original item"


# ============================================================================ #
# Form Rendering & Pre-population Tests
# ============================================================================ #

def test_edit_expense_get_renders_prepopulated_fields(client, test_user):
    """GET /expenses/<id>/edit renders template pre-populated with existing expense data."""
    with app.app_context():
        exp_id = create_expense(
            user_id=test_user["id"],
            amount=145.25,
            category="Health",
            date="2026-08-04",
            description="Dentist checkup",
        )

    with client.session_transaction() as sess:
        sess["user_id"] = test_user["id"]
        sess["user_name"] = test_user["name"]

    response = client.get(f"/expenses/{exp_id}/edit")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "Edit Expense" in html
    assert "145.25" in html
    assert "Health" in html
    assert "2026-08-04" in html
    assert "Dentist checkup" in html
    assert "Save Changes" in html


# ============================================================================ #
# Valid Submission Tests
# ============================================================================ #

def test_edit_expense_post_valid_updates_and_redirects(client, test_user):
    """Submitting valid updates persists changes in SQLite and redirects to /profile with flash."""
    with app.app_context():
        exp_id = create_expense(
            user_id=test_user["id"],
            amount=60.00,
            category="Entertainment",
            date="2026-08-05",
            description="Bowling night",
        )

    with client.session_transaction() as sess:
        sess["user_id"] = test_user["id"]
        sess["user_name"] = test_user["name"]

    response = client.post(
        f"/expenses/{exp_id}/edit",
        data={
            "amount": "85.00",
            "category": "Entertainment",
            "date": "2026-08-06",
            "description": "Bowling night with drinks",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "Expense updated successfully!" in html
    assert "85.00" in html
    assert "Bowling night with drinks" in html

    # Verify DB record
    with app.app_context():
        exp = get_expense_by_id(exp_id)
        assert exp["amount"] == 85.00
        assert exp["date"] == "2026-08-06"
        assert exp["description"] == "Bowling night with drinks"


# ============================================================================ #
# Input Validation Error Handling Tests
# ============================================================================ #

def test_edit_expense_post_validation_missing_fields(client, test_user):
    """Submitting empty amount or category re-renders form with error and entered values."""
    with app.app_context():
        exp_id = create_expense(
            user_id=test_user["id"],
            amount=30.00,
            category="Food",
            date="2026-08-05",
            description="Snack",
        )

    with client.session_transaction() as sess:
        sess["user_id"] = test_user["id"]
        sess["user_name"] = test_user["name"]

    # Empty amount
    res_empty_amount = client.post(
        f"/expenses/{exp_id}/edit",
        data={
            "amount": "",
            "category": "Food",
            "date": "2026-08-05",
            "description": "Updated snack note",
        },
    )
    assert res_empty_amount.status_code == 200
    html = res_empty_amount.get_data(as_text=True)
    assert "Amount, Category, and Date are required." in html
    assert "Updated snack note" in html

    # Empty category
    res_empty_cat = client.post(
        f"/expenses/{exp_id}/edit",
        data={
            "amount": "40.00",
            "category": "",
            "date": "2026-08-05",
            "description": "Snack",
        },
    )
    assert res_empty_cat.status_code == 200
    assert "Amount, Category, and Date are required." in res_empty_cat.get_data(as_text=True)


def test_edit_expense_post_validation_invalid_amount(client, test_user):
    """Submitting negative, zero, or non-numeric amount renders clear validation error."""
    with app.app_context():
        exp_id = create_expense(
            user_id=test_user["id"],
            amount=50.00,
            category="Food",
            date="2026-08-05",
            description="Dinner",
        )

    with client.session_transaction() as sess:
        sess["user_id"] = test_user["id"]
        sess["user_name"] = test_user["name"]

    # Negative amount
    res_neg = client.post(
        f"/expenses/{exp_id}/edit",
        data={
            "amount": "-25.00",
            "category": "Food",
            "date": "2026-08-05",
            "description": "Dinner",
        },
    )
    assert res_neg.status_code == 200
    assert "Please enter a valid positive amount." in res_neg.get_data(as_text=True)

    # Zero amount
    res_zero = client.post(
        f"/expenses/{exp_id}/edit",
        data={
            "amount": "0",
            "category": "Food",
            "date": "2026-08-05",
            "description": "Dinner",
        },
    )
    assert res_zero.status_code == 200
    assert "Please enter a valid positive amount." in res_zero.get_data(as_text=True)

    # Non-numeric string
    res_text = client.post(
        f"/expenses/{exp_id}/edit",
        data={
            "amount": "xyz",
            "category": "Food",
            "date": "2026-08-05",
            "description": "Dinner",
        },
    )
    assert res_text.status_code == 200
    assert "Please enter a valid positive amount." in res_text.get_data(as_text=True)


def test_edit_expense_post_validation_invalid_category(client, test_user):
    """Submitting invalid category rejected with validation message."""
    with app.app_context():
        exp_id = create_expense(
            user_id=test_user["id"],
            amount=50.00,
            category="Food",
            date="2026-08-05",
            description="Dinner",
        )

    with client.session_transaction() as sess:
        sess["user_id"] = test_user["id"]
        sess["user_name"] = test_user["name"]

    response = client.post(
        f"/expenses/{exp_id}/edit",
        data={
            "amount": "50.00",
            "category": "InvalidCategoryName",
            "date": "2026-08-05",
            "description": "Dinner",
        },
    )
    assert response.status_code == 200
    assert "Please select a valid expense category." in response.get_data(as_text=True)


def test_edit_expense_post_validation_invalid_date(client, test_user):
    """Submitting invalid date format rejected with validation message."""
    with app.app_context():
        exp_id = create_expense(
            user_id=test_user["id"],
            amount=50.00,
            category="Food",
            date="2026-08-05",
            description="Dinner",
        )

    with client.session_transaction() as sess:
        sess["user_id"] = test_user["id"]
        sess["user_name"] = test_user["name"]

    response = client.post(
        f"/expenses/{exp_id}/edit",
        data={
            "amount": "50.00",
            "category": "Food",
            "date": "05/08/2026",
            "description": "Dinner",
        },
    )
    assert response.status_code == 200
    assert "Please enter a valid date in YYYY-MM-DD format." in response.get_data(as_text=True)


# ============================================================================ #
# Dashboard Integration & Edit Link UI Tests
# ============================================================================ #

def test_profile_table_has_edit_action_links(client, test_user):
    """Profile page Recent Transactions table includes an Edit link for each transaction."""
    with app.app_context():
        exp_id = create_expense(
            user_id=test_user["id"],
            amount=120.00,
            category="Bills",
            date="2026-08-08",
            description="Water Utility",
        )

    with client.session_transaction() as sess:
        sess["user_id"] = test_user["id"]
        sess["user_name"] = test_user["name"]

    response = client.get("/profile")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert f"/expenses/{exp_id}/edit" in html
    assert "ACTIONS" in html
    assert "Edit" in html


def test_edit_expense_updates_dashboard_statistics(client, test_user):
    """Editing an expense updates the profile total spent and category breakdown."""
    with app.app_context():
        exp_id = create_expense(
            user_id=test_user["id"],
            amount=100.00,
            category="Food",
            date="2026-08-01",
            description="Initial grocery",
        )

    with client.session_transaction() as sess:
        sess["user_id"] = test_user["id"]
        sess["user_name"] = test_user["name"]

    # Initial profile check
    res_init = client.get("/profile")
    assert "100.00" in res_init.get_data(as_text=True)

    # Edit expense to 250.00 under Shopping
    client.post(
        f"/expenses/{exp_id}/edit",
        data={
            "amount": "250.00",
            "category": "Shopping",
            "date": "2026-08-01",
            "description": "Updated to new clothes",
        },
        follow_redirects=True,
    )

    res_updated = client.get("/profile")
    html_updated = res_updated.get_data(as_text=True)

    assert "250.00" in html_updated
    assert "Shopping" in html_updated
    assert "Updated to new clothes" in html_updated

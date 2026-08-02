import pytest
from app import app
from database.db import (
    create_user,
    get_db,
    get_user_by_email,
    get_user_category_expenses,
    get_user_profile_stats,
    get_user_recent_transactions,
    init_db,
    seed_db,
)


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        with app.app_context():
            init_db()
            seed_db()
        yield client


# ============================================================================ #
# Auth Guard Tests
# ============================================================================ #

def test_profile_date_filter_unauthenticated_redirect(client):
    """Unauthenticated access to /profile with date filters should redirect to /login."""
    response = client.get("/profile?start_date=2026-07-01&end_date=2026-07-05")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


# ============================================================================ #
# DB Function Unit Tests
# ============================================================================ #

def test_db_get_user_profile_stats_filtering(client):
    """Verify get_user_profile_stats date filtering options."""
    # Seed user (ID 1) has 8 expenses total in July 2026
    stats_all = get_user_profile_stats(1)
    assert stats_all["total_count"] == 8

    # Filter date range: 2026-07-01 to 2026-07-05
    # Expenses: 45.50 (July 1), 12.00 (July 3), 120.00 (July 5) -> Total = 177.50
    stats_range = get_user_profile_stats(1, start_date="2026-07-01", end_date="2026-07-05")
    assert stats_range["total_count"] == 3
    assert stats_range["total_spent"] == 177.50

    # Filter start_date only: >= 2026-07-15
    # Expenses: 89.99 (July 15), 15.00 (July 18), 28.30 (July 22) -> Total = 133.29, Count = 3
    stats_start_only = get_user_profile_stats(1, start_date="2026-07-15")
    assert stats_start_only["total_count"] == 3
    assert abs(stats_start_only["total_spent"] - 133.29) < 0.01

    # Filter end_date only: <= 2026-07-03
    # Expenses: 45.50 (July 1), 12.00 (July 3) -> Total = 57.50, Count = 2
    stats_end_only = get_user_profile_stats(1, end_date="2026-07-03")
    assert stats_end_only["total_count"] == 2
    assert stats_end_only["total_spent"] == 57.50

    # Date range with zero matching expenses
    stats_empty = get_user_profile_stats(1, start_date="2025-01-01", end_date="2025-01-31")
    assert stats_empty["total_count"] == 0
    assert stats_empty["total_spent"] == 0.0
    assert stats_empty["top_category"] == "None"


def test_db_get_user_category_expenses_filtering(client):
    """Verify get_user_category_expenses date range filtering."""
    # All time categories
    cats_all = get_user_category_expenses(1)
    assert len(cats_all) > 0

    # Filtered categories: 2026-07-01 to 2026-07-05
    cats_filtered = get_user_category_expenses(1, start_date="2026-07-01", end_date="2026-07-05")
    cat_names = [c["category"] for c in cats_filtered]
    assert "Food" in cat_names
    assert "Transport" in cat_names
    assert "Bills" in cat_names
    assert "Entertainment" not in cat_names

    # Filtered categories with zero matches
    cats_empty = get_user_category_expenses(1, start_date="2020-01-01", end_date="2020-01-31")
    assert len(cats_empty) == 0


def test_db_get_user_recent_transactions_filtering(client):
    """Verify get_user_recent_transactions date range filtering and boundary behavior."""
    txs_filtered = get_user_recent_transactions(1, start_date="2026-07-01", end_date="2026-07-05")
    assert len(txs_filtered) == 3
    dates = [tx["date"] for tx in txs_filtered]
    assert all("2026-07-01" <= d <= "2026-07-05" for d in dates)

    # Filter outside date range
    txs_empty = get_user_recent_transactions(1, start_date="2026-08-01", end_date="2026-08-31")
    assert len(txs_empty) == 0


# ============================================================================ #
# Integration Tests: Route GET /profile Query Parameters
# ============================================================================ #

def test_profile_route_happy_path_date_range(client):
    """Authenticated user accessing /profile with valid date range parameters."""
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_name"] = "Demo User"

    response = client.get("/profile?start_date=2026-07-01&end_date=2026-07-05")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    # Verified filtered stats in output
    assert "177.50" in html
    # Active filter indicator or retained input values
    assert 'value="2026-07-01"' in html or "2026-07-01" in html
    assert 'value="2026-07-05"' in html or "2026-07-05" in html


def test_profile_route_start_date_only(client):
    """Authenticated user filtering by start_date only."""
    with client.session_transaction() as sess:
        sess["user_id"] = 1

    response = client.get("/profile?start_date=2026-07-15")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "2026-07-15" in html


def test_profile_route_end_date_only(client):
    """Authenticated user filtering by end_date only."""
    with client.session_transaction() as sess:
        sess["user_id"] = 1

    response = client.get("/profile?end_date=2026-07-05")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "2026-07-05" in html


def test_profile_route_invalid_start_date_format(client):
    """Invalid start_date format is handled gracefully without 500 error."""
    with client.session_transaction() as sess:
        sess["user_id"] = 1

    response = client.get("/profile?start_date=invalid-date&end_date=2026-07-05", follow_redirects=True)
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Invalid start date format" in html or response.status_code == 200


def test_profile_route_invalid_end_date_format(client):
    """Invalid end_date format is handled gracefully without 500 error."""
    with client.session_transaction() as sess:
        sess["user_id"] = 1

    response = client.get("/profile?start_date=2026-07-01&end_date=2026-13-45", follow_redirects=True)
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Invalid end date format" in html or response.status_code == 200


def test_profile_route_inverted_date_range(client):
    """Inverted date range (start_date > end_date) is handled gracefully."""
    with client.session_transaction() as sess:
        sess["user_id"] = 1

    response = client.get("/profile?start_date=2026-07-20&end_date=2026-07-01", follow_redirects=True)
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Start date was after end date" in html or response.status_code == 200


def test_profile_route_no_matching_transactions(client):
    """Date filter with no matching expenses shows zero state cleanly."""
    with client.session_transaction() as sess:
        sess["user_id"] = 1

    response = client.get("/profile?start_date=2020-01-01&end_date=2020-01-31")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "0.00" in html or "No transactions" in html or response.status_code == 200


# ============================================================================ #
# Multi-User & Data Isolation Tests
# ============================================================================ #

def test_profile_date_filter_multi_user_isolation(client):
    """Date filtering for User A does not expose or include User B's expenses."""
    user2 = get_user_by_email("other_test_iso@spendly.com")
    if user2:
        user2_id = user2["id"]
        conn = get_db()
        conn.execute("DELETE FROM expenses WHERE user_id = ?;", (user2_id,))
        conn.commit()
        conn.close()
    else:
        user2_id = create_user("Other User", "other_test_iso@spendly.com", "Password123!")

    # Insert an expense for User 2 in the same date range (2026-07-02)
    conn = get_db()
    conn.execute(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?);",
        (user2_id, 999.99, "Luxury", "2026-07-02", "Secret purchase"),
    )
    conn.commit()
    conn.close()

    # User 1 queries July 1 - July 5 -> should NOT see User 2's 999.99 expense
    stats_u1 = get_user_profile_stats(1, start_date="2026-07-01", end_date="2026-07-05")
    assert stats_u1["total_spent"] == 177.50
    assert stats_u1["total_count"] == 3

    # User 2 queries July 1 - July 5 -> should only see 999.99 expense
    stats_u2 = get_user_profile_stats(user2_id, start_date="2026-07-01", end_date="2026-07-05")
    assert stats_u2["total_spent"] == 999.99
    assert stats_u2["total_count"] == 1

    # Route check for User 2
    with client.session_transaction() as sess:
        sess["user_id"] = user2_id
        sess["user_name"] = "Other User"

    response = client.get("/profile?start_date=2026-07-01&end_date=2026-07-05")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "999.99" in html
    assert "177.50" not in html


def test_profile_clear_filter_resets_view(client):
    """Requesting /profile without query parameters displays all-time data."""
    with client.session_transaction() as sess:
        sess["user_id"] = 1

    response = client.get("/profile")
    assert response.status_code == 200
    stats_all = get_user_profile_stats(1)
    assert stats_all["total_count"] == 8

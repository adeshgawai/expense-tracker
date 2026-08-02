import pytest
from app import app
from database.db import (
    get_db,
    init_db,
    seed_db,
    get_user_profile_stats,
    get_user_category_expenses,
    get_user_recent_transactions,
)


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        with app.app_context():
            init_db()
            seed_db()
        yield client


def test_db_date_filtering(client):
    # User 1 is Demo User in seed_db (expenses 2026-07-01 to 2026-07-22)
    stats_all = get_user_profile_stats(1)
    assert stats_all["total_count"] == 8

    # Filter 2026-07-01 to 2026-07-05: 45.50 + 12.00 + 120.00 = 177.50
    stats_filtered = get_user_profile_stats(1, start_date="2026-07-01", end_date="2026-07-05")
    assert stats_filtered["total_count"] == 3
    assert stats_filtered["total_spent"] == 177.50

    cats_filtered = get_user_category_expenses(1, start_date="2026-07-01", end_date="2026-07-05")
    assert len(cats_filtered) == 3

    txs_filtered = get_user_recent_transactions(1, start_date="2026-07-01", end_date="2026-07-05")
    assert len(txs_filtered) == 3


def test_profile_route_date_filtering(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_name"] = "Demo User"

    response = client.get("/profile?start_date=2026-07-01&end_date=2026-07-05")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "₹177.50" in html
    assert "Active Filter: 2026-07-01 to 2026-07-05" in html


def test_profile_route_inverted_dates(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 1

    response = client.get("/profile?start_date=2026-07-10&end_date=2026-07-01", follow_redirects=True)
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Start date was after end date" in html


def test_profile_route_invalid_date_format(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 1

    response = client.get("/profile?start_date=invalid-date", follow_redirects=True)
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Invalid start date format" in html

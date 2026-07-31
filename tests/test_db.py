import sqlite3
import pytest
from werkzeug.security import check_password_hash

from database.db import get_db, init_db, seed_db


def test_get_db_connection():
    conn = get_db()
    assert isinstance(conn, sqlite3.Connection)
    assert conn.row_factory == sqlite3.Row

    # Test foreign keys PRAGMA is enabled
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys;")
    fk_status = cursor.fetchone()[0]
    assert fk_status == 1
    conn.close()


def test_init_db_creates_tables():
    init_db()
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row["name"] for row in cursor.fetchall()]
    assert "users" in tables
    assert "expenses" in tables
    conn.close()


def test_seed_db_populates_data_and_is_idempotent():
    init_db()
    seed_db()

    conn = get_db()
    cursor = conn.cursor()

    # Check demo user
    cursor.execute("SELECT * FROM users WHERE email = 'demo@spendly.com';")
    user = cursor.fetchone()
    assert user is not None
    assert user["name"] == "Demo User"
    assert check_password_hash(user["password_hash"], "demo123")

    # Check sample expenses
    cursor.execute("SELECT COUNT(*) as count FROM expenses WHERE user_id = ?;", (user["id"],))
    count = cursor.fetchone()["count"]
    assert count == 8

    # Verify categories present
    cursor.execute("SELECT DISTINCT category FROM expenses WHERE user_id = ?;", (user["id"],))
    categories = {row["category"] for row in cursor.fetchall()}
    expected_categories = {"Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"}
    assert expected_categories.issubset(categories)

    conn.close()

    # Run seed_db again to test idempotency
    seed_db()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM users;")
    assert cursor.fetchone()["count"] == 1
    cursor.execute("SELECT COUNT(*) as count FROM expenses;")
    assert cursor.fetchone()["count"] == 8
    conn.close()


def test_foreign_key_constraint():
    init_db()
    conn = get_db()
    cursor = conn.cursor()

    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            "INSERT INTO expenses (user_id, amount, category, date) VALUES (?, ?, ?, ?);",
            (99999, 50.0, "Food", "2026-07-01"),
        )
    conn.close()


def test_unique_email_constraint():
    init_db()
    seed_db()
    conn = get_db()
    cursor = conn.cursor()

    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?);",
            ("Another User", "demo@spendly.com", "hash123"),
        )
    conn.close()

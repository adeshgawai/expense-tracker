import os
import sqlite3
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "spendly.db")


def get_db():
    """Returns a SQLite connection with row_factory and foreign keys enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """Creates users and expenses tables using CREATE TABLE IF NOT EXISTS."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)
    conn.commit()
    conn.close()


def seed_db():
    """Inserts sample user and expenses data if database is empty."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users;")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    # Seed demo user
    demo_pass = generate_password_hash("demo123")
    cursor.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?);",
        ("Demo User", "demo@spendly.com", demo_pass),
    )
    user_id = cursor.lastrowid

    # Seed sample expenses across categories
    sample_expenses = [
        (user_id, 45.50, "Food", "2026-07-01", "Grocery shopping"),
        (user_id, 12.00, "Transport", "2026-07-03", "Subway pass"),
        (user_id, 120.00, "Bills", "2026-07-05", "Electricity bill"),
        (user_id, 35.00, "Health", "2026-07-08", "Pharmacy visit"),
        (user_id, 25.00, "Entertainment", "2026-07-12", "Movie tickets"),
        (user_id, 89.99, "Shopping", "2026-07-15", "New shoes"),
        (user_id, 15.00, "Other", "2026-07-18", "Book store"),
        (user_id, 28.30, "Food", "2026-07-22", "Dinner with friends"),
    ]
    cursor.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?);",
        sample_expenses,
    )
    conn.commit()
    conn.close()


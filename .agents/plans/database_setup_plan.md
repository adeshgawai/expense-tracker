# Implementation Plan — Step 1: Database Setup

Replace the placeholder stub in `database/db.py` with a working SQLite data layer and wire it into Flask application startup (`app.py`).

---

## Goal Description
Implement the database initialization, schema definition (`users` and `expenses` tables), and seed data seeding for Spendly. Ensure connection helpers set proper SQLite pragmas (`PRAGMA foreign_keys = ON`, `row_factory = sqlite3.Row`) and use strictly parameterized SQL queries.

---

## User Review Required

> [!NOTE]
> Database File Name: The SQLite database file will be created in the project root as `spendly.db`.

> [!IMPORTANT]
> Password Hashing: Hashing the demo user (`demo@spendly.com`) password (`demo123`) using `werkzeug.security.generate_password_hash`.

---

## Open Questions

- None at present. If you would like to customize the database file name or default seed expenses, please let us know!

---

## Proposed Changes

### Database Layer

#### [MODIFY] `database/db.py`
- Implement `get_db()`:
  - Connect to `spendly.db` in project root
  - Set `conn.row_factory = sqlite3.Row`
  - Execute `PRAGMA foreign_keys = ON;`
  - Return connection
- Implement `init_db()`:
  - Execute `CREATE TABLE IF NOT EXISTS users (...)`
  - Execute `CREATE TABLE IF NOT EXISTS expenses (...)`
  - Table schemas:
    - **`users`**: `id` (INTEGER PRIMARY KEY AUTOINCREMENT), `name` (TEXT NOT NULL), `email` (TEXT UNIQUE NOT NULL), `password_hash` (TEXT NOT NULL), `created_at` (TEXT DEFAULT (datetime('now')))
    - **`expenses`**: `id` (INTEGER PRIMARY KEY AUTOINCREMENT), `user_id` (INTEGER NOT NULL, FK to users.id), `amount` (REAL NOT NULL), `category` (TEXT NOT NULL), `date` (TEXT NOT NULL), `description` (TEXT), `created_at` (TEXT DEFAULT (datetime('now')))
- Implement `seed_db()`:
  - Check if `users` table has existing records; if so, skip seeding.
  - Insert Demo User: name="Demo User", email="demo@spendly.com", password_hash via `generate_password_hash("demo123")`
  - Insert 8 sample expenses covering all required categories (`Food`, `Transport`, `Bills`, `Health`, `Entertainment`, `Shopping`, `Other`) with valid `YYYY-MM-DD` dates.

```python
import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "spendly.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
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
        ("Demo User", "demo@spendly.com", demo_pass)
    )
    user_id = cursor.lastrowid

    # Seed sample expenses
    sample_expenses = [
        (user_id, 45.50, "Food", "2026-07-01", "Grocery shopping"),
        (user_id, 12.00, "Transport", "2026-07-03", "Subway pass"),
        (user_id, 120.00, "Bills", "2026-07-05", "Electricity bill"),
        (user_id, 35.00, "Health", "2026-07-08", "Pharmacy visit"),
        (user_id, 25.00, "Entertainment", "2026-07-12", "Movie tickets"),
        (user_id, 89.99, "Shopping", "2026-07-15", "New shoes"),
        (user_id, 15.00, "Other", "2026-07-18", "Book store"),
        (user_id, 28.30, "Food", "2026-07-22", "Dinner with friends")
    ]
    cursor.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?);",
        sample_expenses
    )
    conn.commit()
    conn.close()
```

---

### Application Entry Point

#### [MODIFY] `app.py`
- Import `init_db` and `seed_db` from `database.db`.
- Initialize database tables and seed data inside `with app.app_context():`.

```python
from database.db import init_db, seed_db

# Wire database initialization into application startup
with app.app_context():
    init_db()
    seed_db()
```

---

## Verification Plan

### Automated Tests
1. Create a test module `tests/test_db.py` to verify:
   - `get_db()` returns valid connection with `row_factory` set and foreign keys enabled.
   - `init_db()` creates `users` and `expenses` tables.
   - `seed_db()` inserts 1 user and 8 expenses, and calling `seed_db()` a second time does not duplicate rows.
   - Foreign key constraint failure when inserting expense with nonexistent `user_id`.
   - Unique constraint failure when inserting duplicate email into `users`.
2. Run pytest:
   ```bash
   pytest
   ```

### Manual Verification
1. Start application server with `python app.py` (or `uv run python app.py`).
2. Verify `spendly.db` is created in root directory.
3. Query SQLite DB to verify tables and seeded records.

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


def get_user_by_email(email):
    """Fetches a user record by email address (case-insensitive)."""
    conn = get_db()
    cursor = conn.cursor()
    clean_email = email.strip().lower() if email else ""
    cursor.execute("SELECT * FROM users WHERE LOWER(email) = ?;", (clean_email,))
    user = cursor.fetchone()
    conn.close()
    return user


def create_user(name, email, password):
    """Creates a new user with werkzeug password hashing and returns inserted user_id."""
    conn = get_db()
    cursor = conn.cursor()
    clean_name = name.strip() if name else ""
    clean_email = email.strip().lower() if email else ""
    password_hash = generate_password_hash(password)

    cursor.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?);",
        (clean_name, clean_email, password_hash),
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return user_id


def get_user_by_id(user_id):
    """Fetches a user record by user ID."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, created_at FROM users WHERE id = ?;", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user


def _build_user_date_where(user_id, start_date=None, end_date=None):
    """Helper to build WHERE clause and parameter list for user date filtering."""
    query_where = ["user_id = ?"]
    params = [user_id]

    if start_date:
        query_where.append("date >= ?")
        params.append(start_date)
    if end_date:
        query_where.append("date <= ?")
        params.append(end_date)

    where_clause = " AND ".join(query_where)
    return where_clause, params


def get_user_profile_stats(user_id, start_date=None, end_date=None):
    """Returns summary stats (total_count, total_spent, top_category) for a given user, optionally filtered by date range."""
    conn = get_db()
    cursor = conn.cursor()

    where_clause, params = _build_user_date_where(user_id, start_date, end_date)

    cursor.execute(
        f"""
        SELECT 
            COUNT(*) as total_count,
            COALESCE(SUM(amount), 0.0) as total_spent
        FROM expenses 
        WHERE {where_clause};
        """,
        params,
    )
    row = cursor.fetchone()
    total_count = row["total_count"] if row else 0
    total_spent = row["total_spent"] if row else 0.0

    cursor.execute(
        f"""
        SELECT category
        FROM expenses
        WHERE {where_clause}
        GROUP BY category
        ORDER BY SUM(amount) DESC
        LIMIT 1;
        """,
        params,
    )
    top_cat_row = cursor.fetchone()
    top_category = top_cat_row["category"] if top_cat_row else "None"

    conn.close()
    return {
        "total_count": total_count,
        "total_spent": total_spent,
        "top_category": top_category,
    }


def get_user_category_expenses(user_id, start_date=None, end_date=None):
    """Returns category-wise spending breakdown (category, item_count, category_total) for a given user, optionally filtered by date range."""
    conn = get_db()
    cursor = conn.cursor()

    where_clause, params = _build_user_date_where(user_id, start_date, end_date)

    cursor.execute(
        f"""
        SELECT 
            category,
            COUNT(*) as item_count,
            COALESCE(SUM(amount), 0.0) as category_total
        FROM expenses
        WHERE {where_clause}
        GROUP BY category
        ORDER BY category_total DESC;
        """,
        params,
    )
    categories = cursor.fetchall()
    conn.close()
    return categories


def get_user_recent_transactions(user_id, limit=10, start_date=None, end_date=None):
    """Returns recent expenses for a given user sorted by date descending, optionally filtered by date range."""
    conn = get_db()
    cursor = conn.cursor()

    where_clause, params = _build_user_date_where(user_id, start_date, end_date)
    params_with_limit = params + [limit]

    cursor.execute(
        f"""
        SELECT id, amount, category, date, description
        FROM expenses
        WHERE {where_clause}
        ORDER BY date DESC, id DESC
        LIMIT ?;
        """,
        params_with_limit,
    )
    transactions = cursor.fetchall()
    conn.close()
    return transactions


def create_expense(user_id, amount, category, date, description=""):
    """Inserts a new expense record for a user using parameterized query and returns inserted expense id."""
    conn = get_db()
    cursor = conn.cursor()
    clean_desc = description.strip() if description else ""
    cursor.execute(
        """
        INSERT INTO expenses (user_id, amount, category, date, description)
        VALUES (?, ?, ?, ?, ?);
        """,
        (user_id, float(amount), category.strip(), date.strip(), clean_desc),
    )
    expense_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return expense_id


def get_expense_by_id(expense_id, user_id=None):
    """Fetches an expense by ID, optionally verifying ownership by user_id."""
    conn = get_db()
    cursor = conn.cursor()
    if user_id is not None:
        cursor.execute("SELECT * FROM expenses WHERE id = ? AND user_id = ?;", (expense_id, user_id))
    else:
        cursor.execute("SELECT * FROM expenses WHERE id = ?;", (expense_id,))
    expense = cursor.fetchone()
    conn.close()
    return expense


def update_expense(expense_id, user_id, amount, category, date, description=""):
    """Updates an expense record for a specific user using parameterized query."""
    conn = get_db()
    cursor = conn.cursor()
    clean_desc = description.strip() if description else ""
    cursor.execute(
        """
        UPDATE expenses
        SET amount = ?, category = ?, date = ?, description = ?
        WHERE id = ? AND user_id = ?;
        """,
        (float(amount), category.strip(), date.strip(), clean_desc, expense_id, user_id),
    )
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    return rows_affected > 0


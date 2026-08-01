# Implementation Plan - Step 04: Profile Page Design

This plan details the implementation of the user profile page (`GET /profile`) for Spendly, building upon the database setup (Step 01), registration (Step 02), and login/logout authentication (Step 03).

## Goal Description
Implement the `/profile` (GET) route handler in `app.py`, add database queries in `database/db.py` for fetching user details and expenditure metrics, create the `templates/profile.html` template adhering to Spendly design system, add custom styling in `static/css/style.css`, and implement test coverage in `tests/test_profile.py`.

## User Review Required
> [!NOTE]
> No database schema modifications are needed for this step. Data is retrieved from the existing `users` and `expenses` tables created in Step 01.

## Proposed Changes

### Database Layer (`database/db.py`)
#### [MODIFY] [`database/db.py`](file:///E:/Agentic%20AI/Agentic%20coding/expense-tracker/database/db.py)
- Implement `get_user_by_id(user_id)` helper function returning user record (`id`, `name`, `email`, `created_at`).
- Implement `get_user_profile_stats(user_id)` helper function returning total expense count (`total_count`) and total amount spent (`total_spent`) using `COALESCE(SUM(amount), 0.0)`.

```python
def get_user_by_id(user_id):
    """Fetches a user record by user ID."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, created_at FROM users WHERE id = ?;", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user


def get_user_profile_stats(user_id):
    """Returns summary stats (total_count, total_spent) for a given user."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT 
            COUNT(*) as total_count,
            COALESCE(SUM(amount), 0.0) as total_spent
        FROM expenses 
        WHERE user_id = ?;
        """,
        (user_id,),
    )
    stats = cursor.fetchone()
    conn.close()
    return stats
```

---

### Application Layer (`app.py`)
#### [MODIFY] [`app.py`](file:///E:/Agentic%20AI/Agentic%20coding/expense-tracker/app.py)
- Update imports from `database.db` to include `get_user_by_id` and `get_user_profile_stats`.
- Update `@app.route("/profile")` handler:
  - Verify `user_id = session.get("user_id")`.
  - If unauthenticated, flash `"Please log in to access your profile."` with category `"warning"` and redirect to `url_for("login")`.
  - Fetch user with `get_user_by_id(user_id)`. If user is missing, clear `session`, flash warning, and redirect to `login`.
  - Fetch stats with `get_user_profile_stats(user_id)`.
  - Render `profile.html` with `user` and `stats`.

```python
from database.db import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    get_user_profile_stats,
    init_db,
    seed_db,
)

@app.route("/profile")
def profile():
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in to access your profile.", "warning")
        return redirect(url_for("login"))

    user = get_user_by_id(user_id)
    if not user:
        session.clear()
        flash("User account not found. Please log in again.", "warning")
        return redirect(url_for("login"))

    stats = get_user_profile_stats(user_id)
    return render_template("profile.html", user=user, stats=stats)
```

---

### Template Layer (`templates/`)
#### [NEW] [`templates/profile.html`](file:///E:/Agentic%20AI/Agentic%20coding/expense-tracker/templates/profile.html)
- Extends `base.html`.
- Implements profile header banner with user initials avatar, user full name, email badge, and member registration date.
- Implements expenditure summary stats grid (Total Expenses Count & Total Amount Spent formatted in Rupees `₹`).
- Implements Account Information card listing profile details.
- Implements Quick Action bar with links to Add Expense (`url_for('add_expense')`) and Sign Out (`url_for('logout')`).

---

### Stylesheet Layer (`static/css/style.css`)
#### [MODIFY] [`static/css/style.css`](file:///E:/Agentic%20AI/Agentic%20coding/expense-tracker/static/css/style.css)
- Add CSS rules for `.profile-hero`, `.profile-avatar`, `.profile-stats-grid`, `.stat-card`, `.stat-value`, `.stat-label`, `.profile-card`, and `.profile-actions`.
- Use existing CSS variables (`--paper-card`, `--accent`, `--accent-light`, `--border`, `--font-display`, etc.) to maintain visual harmony.

---

### Test Suite (`tests/`)
#### [NEW] [`tests/test_profile.py`](file:///E:/Agentic%20AI/Agentic%20coding/expense-tracker/tests/test_profile.py)
Create tests covering:
- `test_profile_unauthenticated_redirects`: Unauthenticated `GET /profile` redirects to `/login`.
- `test_profile_authenticated_renders`: Authenticated `GET /profile` renders `profile.html` (HTTP 200).
- `test_profile_displays_user_data_and_stats`: Renders user name, email, and accurate expense count/sum.
- `test_profile_invalid_user_session`: Redirects to `/login` if `user_id` in session does not exist in DB.

## Verification Plan

### Automated Tests
Run `pytest` to execute all tests (including new `test_profile.py`):
```bash
pytest
```

### Manual Verification
1. Access `http://127.0.0.1:5001/profile` while logged out -> verify redirect to `/login` with flash alert.
2. Sign in as demo user (`demo@spendly.com` / `demo123`).
3. Click "Profile" in navbar -> verify avatar initials, account details, and expense metrics display correctly.

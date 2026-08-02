# Implementation Plan - Date Filter for Profile Page

This plan outlines the technical design and steps required to implement **Date Range Filtering** on the user profile dashboard (`/profile`). Users will be able to filter their summary metrics, category spending breakdown, and transaction list by custom date ranges or quick presets.

## Goal Description
Enhance the `/profile` dashboard with date range filtering capabilities (`start_date` and `end_date`), allowing logged-in users to filter spending statistics, category breakdowns, and transaction history. The feature includes quick preset buttons ("This Month", "Last 30 Days", "This Year", "All Time"), date validation, reset functionality, and responsive UI design.

## User Review Required

> [!IMPORTANT]
> - **Query Parameter format**: `start_date` and `end_date` will use standard `YYYY-MM-DD` string format, matching HTML `<input type="date">`.
> - **Date Inversion Handling**: If `start_date` > `end_date`, the backend will automatically swap them or render a flash warning while ensuring no database errors occur.
> - **Presets Interaction**: Quick preset buttons will populate the date input fields and automatically submit the form via Vanilla JavaScript, without requiring external libraries.

## Proposed Changes

---

### Database Layer

#### [MODIFY] [`database/db.py`](file:///E:/Agentic%20AI/Agentic%20coding/expense-tracker/database/db.py)
Update SQL queries to support optional `start_date` and `end_date` parameters using parameterized queries (`WHERE date >= ? AND date <= ?`).

```python
def get_user_profile_stats(user_id, start_date=None, end_date=None):
    # Dynamically build SQL parameters safely:
    # SQL: SELECT COUNT(*) as total_count, COALESCE(SUM(amount), 0.0) as total_spent FROM expenses WHERE user_id = ?
    # Add AND date >= ? if start_date
    # Add AND date <= ? if end_date
    ...

def get_user_category_expenses(user_id, start_date=None, end_date=None):
    # Filter category aggregate by user_id and optional date range
    ...

def get_user_recent_transactions(user_id, limit=10, start_date=None, end_date=None):
    # Filter transactions by user_id and optional date range
    ...
```

---

### Application Layer

#### [MODIFY] [`app.py`](file:///E:/Agentic%20AI/Agentic%20coding/expense-tracker/app.py)
- Add a helper function `validate_date_string(date_str)` to validate `YYYY-MM-DD` format.
- Update `/profile` route handler to extract `start_date` and `end_date` from `request.args`.
- Pass `start_date`, `end_date`, and calculated preset flags to `render_template("profile.html", ...)`.

```python
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

    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()

    # Validate and handle date logic
    start_date, end_date, date_error = process_date_filters(start_date, end_date)
    if date_error:
        flash(date_error, "warning")

    stats = get_user_profile_stats(user_id, start_date=start_date, end_date=end_date)
    category_expenses = get_user_category_expenses(user_id, start_date=start_date, end_date=end_date)
    recent_transactions = get_user_recent_transactions(user_id, limit=50 if (start_date or end_date) else 10, start_date=start_date, end_date=end_date)

    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        category_expenses=category_expenses,
        recent_transactions=recent_transactions,
        start_date=start_date,
        end_date=end_date,
    )
```

---

### Template & Frontend Layer

#### [MODIFY] [`templates/profile.html`](file:///E:/Agentic%20AI/Agentic%20coding/expense-tracker/templates/profile.html)
Add a date filter control card above the metrics section:
- Inputs for `start_date` and `end_date` (`<input type="date">`).
- Action buttons: "Filter" and "Reset".
- Quick preset buttons ("This Month", "Last 30 Days", "This Year", "All Time").
- Active filter pill displaying the current active date range and option to clear filter.

#### [MODIFY] [`static/css/style.css`](file:///E:/Agentic%20AI/Agentic%20coding/expense-tracker/static/css/style.css)
Add CSS rules for date filter toolbar:
- `.date-filter-card` card design aligned with Spendly design system (variables: `--paper-card`, `--border`, `--accent`, `--ink`).
- `.date-filter-form` layout (flexbox / grid layout with responsive wrapping).
- Preset chip styles with active/hover states.

#### [MODIFY] [`static/js/main.js`](file:///E:/Agentic%20AI/Agentic%20coding/expense-tracker/static/js/main.js)
Add date preset event listeners:
- Preset buttons automatically set `start_date` and `end_date` inputs based on current date calculations and submit the form.

---

### Testing Layer

#### [NEW] [`tests/test_date_filter.py`](file:///E:/Agentic%20AI/Agentic%20coding/expense-tracker/tests/test_date_filter.py)
Create unit and integration tests using pytest and Flask test client:
- Test DB helper functions with start/end date ranges.
- Test GET `/profile` with valid `start_date` and `end_date`.
- Test GET `/profile` with start_date > end_date.
- Test GET `/profile` with invalid date strings (e.g. `start_date=invalid`).
- Verify returned transactions and total spent amounts match expected date ranges.

## Verification Plan

### Automated Tests
Run pytest suite to verify logic and route responses:
```bash
pytest tests/test_date_filter.py
```

### Manual Verification
1. Log into Spendly (e.g. `demo@spendly.com` / `demo123`).
2. Navigate to Profile page (`/profile`).
3. Select custom Start Date (`2026-07-01`) and End Date (`2026-07-10`).
4. Click **Apply Filter** and verify stats, category chart, and transaction table update to show only transactions within that period.
5. Click preset buttons ("This Month", "Last 30 Days", "All Time") and verify dates populate and filter properly.
6. Click **Reset Filter** and verify page reverts to all-time view.

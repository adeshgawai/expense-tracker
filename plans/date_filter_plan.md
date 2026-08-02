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

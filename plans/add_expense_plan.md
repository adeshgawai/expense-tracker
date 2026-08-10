# Implementation Plan - Add Expense (Feature 06)

This plan outlines the technical design, architectural components, and step-by-step implementation strategy for the **Add Expense** feature (`GET /expenses/add` and `POST /expenses/add`) in Spendly.

## Goal Description
Allow authenticated users to record new financial transactions by entering an amount, category, date, and optional description. Adding expenses is Spendly's core transactional action, updating profile metrics (total spent, transaction count, top category), category breakdown distribution, and recent transactions.

```
                    ┌─────────────────────────┐
                    │     User on /profile    │
                    │  Clicks "+ Add Expense" │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │    GET /expenses/add    │
                    │  Renders Form (today)   │
                    └────────────┬────────────┘
                                 │
                         Submits Expense Form
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │    POST /expenses/add   │
                    │   Validates Form Data   │
                    └────────────┬────────────┘
                        ▲                 │
             Invalid    │                 │ Valid
             Inputs     │                 ▼
                    ┌───┴──────────┐  ┌─────────────────────────┐
                    │ Render Form  │  │   database/db.py        │
                    │ with Error   │  │   create_expense(...)   │
                    └──────────────┘  └───────────┬─────────────┘
                                                  │
                                                  ▼
                                      ┌─────────────────────────┐
                                      │   Redirect /profile     │
                                      │   Flash Success Msg     │
                                      └─────────────────────────┘
```

---

## User Review Required

> [!IMPORTANT]
> - **Predefined Categories**: Allowed categories are standardized to `["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"]` to maintain consistency across category breakdown charts and database queries.
> - **Date Default**: The date field on `GET /expenses/add` will automatically default to current date (`YYYY-MM-DD`).
> - **Authentication Gate**: All routes under `/expenses/*` strictly require an authenticated session (`user_id`). Unauthenticated requests redirect to `/login` with an informative warning flash.
> - **Zero & Negative Amount Prevention**: Only strictly positive numbers (`amount > 0`) are permitted.

---

## Proposed Changes

### 1. Database Layer

#### [MODIFY] [`database/db.py`](file:///E:/Agentic%20AI/Agentic%20coding/expense-tracker/database/db.py)
- Implement `create_expense(user_id, amount, category, date, description="")` helper function using parameterized SQLite queries.
- Ensure foreign key constraints and type consistency.

```python
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
```

---

### 2. Application Layer

#### [MODIFY] [`app.py`](file:///E:/Agentic%20AI/Agentic%20coding/expense-tracker/app.py)
- Import `create_expense` from `database.db`.
- Define `ALLOWED_CATEGORIES = ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"]`.
- Replace stub `add_expense()` route with full `GET` and `POST` request handling:
  - Check `session.get("user_id")` (redirect to `/login` if missing).
  - On `GET`: Render `add_expense.html` with default date (`today`) and category list.
  - On `POST`:
    - Validate required fields (`amount`, `category`, `date`).
    - Validate `amount` is a valid positive float (`> 0`).
    - Validate `category` is within `ALLOWED_CATEGORIES`.
    - Validate `date` format using existing `is_valid_date()`.
    - If validation fails, re-render `add_expense.html` with error alert and preserved form values.
    - If valid, execute `create_expense(...)`, set success flash message, and redirect to `profile`.

---

### 3. Template & Presentation Layer

#### [NEW] [`templates/add_expense.html`](file:///E:/Agentic%20AI/Agentic%20coding/expense-tracker/templates/add_expense.html)
- Extend `base.html`.
- Clean, focused transaction creation card matching Spendly design system.
- Amount input with currency symbol adornment (`₹`).
- Dropdown select for Category with styled option items.
- Date picker input defaulting to today (`YYYY-MM-DD`).
- Text input for optional Description (e.g. "Weekly groceries").
- Submit button ("+ Add Expense") and Cancel button linking back to `url_for('profile')`.

#### [MODIFY] [`templates/profile.html`](file:///E:/Agentic%20AI/Agentic%20coding/expense-tracker/templates/profile.html)
- Add primary action button "+ Add Expense" in the profile dashboard header / action toolbar.
- Update empty transactions state message with an active link to `url_for('add_expense')`.

#### [MODIFY] [`static/css/style.css`](file:///E:/Agentic%20AI/Agentic%20coding/expense-tracker/static/css/style.css)
- Add CSS styling for:
  - `.expense-form-container` and `.expense-card`
  - Currency adorned input `.input-currency-wrapper`
  - `.custom-select` dropdown styling
  - Form action button groups and cancel link
  - Responsive layout adjustments for mobile screens

---

### 4. Testing Layer

#### [NEW] [`tests/test_add_expense.py`](file:///E:/Agentic%20AI/Agentic%20coding/expense-tracker/tests/test_add_expense.py)
Automated test suite using `pytest` and Flask test client:
- `test_add_expense_unauthenticated_get_redirects`: Verify `GET /expenses/add` redirects to `/login`.
- `test_add_expense_unauthenticated_post_redirects`: Verify `POST /expenses/add` redirects to `/login`.
- `test_add_expense_get_authenticated`: Verify authenticated user sees form with current date and categories.
- `test_add_expense_post_valid`: Verify submitting valid data persists to DB and redirects to `/profile` with flash.
- `test_add_expense_post_missing_fields`: Verify missing amount, category, or date returns error.
- `test_add_expense_post_invalid_amount`: Verify negative amount, zero, or non-numeric string returns error.
- `test_add_expense_post_invalid_category`: Verify non-allowed category returns error.
- `test_add_expense_post_invalid_date`: Verify invalid date string returns error.
- `test_add_expense_updates_profile_stats`: Verify added expense updates total count, total spent, and category breakdown.

---

## Verification Plan

### Automated Tests
Run pytest across all test suites to guarantee zero regression and 100% feature coverage:
```bash
pytest tests/test_add_expense.py -v
pytest
```

### Manual Verification
1. Start local server with `python app.py`.
2. Login with demo account (`demo@spendly.com` / `demo123`).
3. Click "+ Add Expense" from `/profile`.
4. Verify form displays with today's date pre-filled.
5. Attempt submitting with empty amount, negative amount, or empty fields; verify error feedback.
6. Submit a valid expense (e.g. ₹450.00 for "Food" - "Dinner with team").
7. Verify immediate redirection to `/profile` with success notification.
8. Verify the new transaction appears at the top of Recent Transactions and updates Total Spent & Category stats.

# Spec: Add Expense

## Overview
This feature implements the Add Expense functionality (`GET /expenses/add` and `POST /expenses/add`), allowing logged-in users to record new financial transactions. Users can specify the transaction amount, select a spending category, choose the transaction date (defaulting to today), and provide an optional description. Adding expenses is the core transactional feature of Spendly, dynamically updating the profile dashboard's total spent, transaction count, category breakdown chart, and recent transactions table.

## Depends on
- Step 01: Database Setup (`01-database-setup.md`)
- Step 02: Registration (`02-registration.md`)
- Step 03: Login and Logout (`03-login-logout.md`)
- Step 04: Profile Page (`04-profile-page.md`)
- Step 05: Date Filter for Profile Page (`05-date-filter-profile.md`)

## Routes
- `GET /expenses/add` — Renders the Add Expense form page — Logged-in (redirects unauthenticated users to `/login`)
- `POST /expenses/add` — Validates form data, inserts new expense record for the logged-in user, flashes success message, and redirects to `/profile` — Logged-in (redirects unauthenticated users to `/login`)

## Database changes
No database changes.
(The `expenses` table is already defined in `database/db.py`). A helper function `create_expense(user_id, amount, category, date, description)` will be added to `database/db.py`.

## Templates
- **Create:**
  - `templates/add_expense.html`: Add Expense form page extending `base.html` with fields for Amount, Category, Date, and Description.
- **Modify:**
  - `templates/profile.html`: Add "+ Add Expense" action button in the profile header and empty state view.
  - `templates/base.html`: Ensure navigation links support intuitive access.

## Files to change
- `app.py` — Replace stub `add_expense()` route with full `GET` and `POST` handlers, authentication verification, validation for amount/category/date, and database invocation.
- `database/db.py` — Implement `create_expense(user_id, amount, category, date, description)` using parameterized queries.
- `templates/profile.html` — Add prominent "+ Add Expense" button linking to `url_for('add_expense')`.
- `static/css/style.css` — Add styling for the Add Expense card, input groups, currency adornment, category select, date input, submit buttons, and validation states.

## Files to create
- `.agents/specs/06-add-expense.md` — Feature specification document.
- `templates/add_expense.html` — Jinja2 template for the Add Expense page.
- `tests/test_06_add_expense.py` — Pytest test suite validating authentication protection, form rendering, valid submissions, input validation errors, and database persistence.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Always use `url_for()` for template links and route redirects
- Redirect unauthenticated users to `url_for('login')` with an informative warning flash message
- Validate inputs on server side (amount > 0, category in allowed list, date formatted as YYYY-MM-DD)
- Default date field to current date (`YYYY-MM-DD`) when rendering form

## Definition of done
- [ ] Navigating to `GET /expenses/add` while logged out redirects to `/login` with a warning message.
- [ ] Navigating to `GET /expenses/add` while logged in renders `templates/add_expense.html`.
- [ ] Form contains Amount, Category (Food, Transport, Bills, Health, Entertainment, Shopping, Other), Date (defaults to today), and optional Description.
- [ ] Submitting valid data via `POST /expenses/add` inserts the record into SQLite and redirects to `/profile` with a success flash message.
- [ ] Submitting invalid inputs (empty amount, zero/negative amount, invalid category, invalid date format) displays clear error feedback and preserves valid form fields.
- [ ] Profile dashboard displays the newly created expense in recent transactions, updates total expenditure, transaction counter, and category distribution.
- [ ] Prominent "+ Add Expense" button is accessible on the dashboard (`/profile`).
- [ ] All automated tests in `tests/test_06_add_expense.py` pass cleanly via `pytest`.

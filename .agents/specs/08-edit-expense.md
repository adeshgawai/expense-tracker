# Spec: Edit Expense

## Overview
This feature implements the Edit Expense functionality (`GET /expenses/<id>/edit` and `POST /expenses/<id>/edit`), enabling authenticated users to update existing transaction records (amount, category, date, and description). Allowing users to edit recorded expenses ensures transaction accuracy without having to recreate entries, dynamically recalculating the profile dashboard totals, category breakdowns, and transaction history. Robust authorization ensures users can only access and modify their own expenses.

## Depends on
- Step 01: Database Setup (`01-database-setup.md`)
- Step 02: Registration (`02-registration.md`)
- Step 03: Login and Logout (`03-login-logout.md`)
- Step 04: Profile Page (`04-profile-page.md`)
- Step 05: Date Filter for Profile Page (`05-date-filter-profile.md`)
- Step 06: Add Expense (`06-add-expense.md`)

## Routes
- `GET /expenses/<int:id>/edit` — Renders the Edit Expense form pre-populated with the existing expense details — Logged-in (redirects unauthenticated users to `/login`; returns 404 or redirects with error if expense is not found or belongs to another user)
- `POST /expenses/<int:id>/edit` — Validates updated expense data, updates the record in SQLite for the logged-in user, flashes a success message, and redirects to `/profile` — Logged-in (redirects unauthenticated users to `/login`; rejects unauthorized modifications)

## Database changes
No database changes.
(The `expenses` table is already defined in `database/db.py`). Helper functions `get_expense_by_id(expense_id, user_id=None)` and `update_expense(expense_id, user_id, amount, category, date, description="")` will be added to `database/db.py`.

## Templates
- **Create:**
  - `templates/edit_expense.html`: Edit Expense form page extending `base.html` pre-populated with existing transaction values for Amount, Category, Date, and Description.
- **Modify:**
  - `templates/profile.html`: Add an Actions column or Edit link in the Recent Transactions table linking to `url_for('edit_expense', id=tx['id'])`.

## Files to change
- `app.py` — Replace stub `edit_expense(id)` route with complete `GET` and `POST` handlers, authentication/authorization checks, server-side validation, and database updates.
- `database/db.py` — Implement `get_expense_by_id(expense_id, user_id=None)` and `update_expense(expense_id, user_id, amount, category, date, description="")` using parameterized queries.
- `templates/profile.html` — Add Edit action link to each transaction in the Recent Transactions table.
- `static/css/style.css` — Add styles for transaction action links/buttons and form layout consistency.

## Files to create
- `.agents/specs/08-edit-expense.md` — Feature specification document.
- `templates/edit_expense.html` — Jinja2 template for the Edit Expense page.
- `tests/test_08_edit_expense.py` — Pytest test suite covering authentication protection, ownership authorization, form pre-population, valid updates, validation errors, and database persistence.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Always use `url_for()` for template links and route redirects
- Strict user ownership validation: users can only view and edit their own expenses (prevent IDOR attacks)
- Redirect unauthenticated users to `url_for('login')` with a warning flash message
- If an expense does not exist or does not belong to the logged-in user, abort with 404 or redirect to `url_for('profile')` with an error message
- Validate inputs on server side (positive amount, valid category in allowed categories list, valid YYYY-MM-DD date format)
- Retain updated values in form if validation fails

## Definition of done
- [ ] Navigating to `GET /expenses/<id>/edit` while logged out redirects to `/login` with a warning message.
- [ ] Navigating to `GET /expenses/<id>/edit` for a non-existent expense or an expense belonging to another user returns 404 or redirects to `/profile` with an error message.
- [ ] Navigating to `GET /expenses/<id>/edit` with valid ownership loads `templates/edit_expense.html` with fields pre-populated with the expense's current amount, category, date, and description.
- [ ] Submitting valid changes via `POST /expenses/<id>/edit` updates the expense record in SQLite and redirects to `/profile` with a success flash message.
- [ ] Submitting invalid changes (empty amount, non-positive amount, invalid category, invalid date) displays clear error feedback and preserves user inputs.
- [ ] Profile dashboard reflects updated expense amounts, dates, descriptions, and category totals.
- [ ] Each transaction in the Recent Transactions table on `/profile` includes a clickable "Edit" link.
- [ ] All automated tests in `tests/test_08_edit_expense.py` pass cleanly via `pytest`.

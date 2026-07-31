# Spec: Registration

## Overview
Implement user account registration for the Spendly expense tracker. This feature enables new users to sign up by submitting their full name, email address, and password via the `/register` form. Successful registration validates input, verifies email uniqueness, securely hashes the password using `werkzeug.security.generate_password_hash`, saves the user record in SQLite via database helper functions, establishes a user session, and redirects the user to the application dashboard/landing page with a success confirmation. If validation fails or the email is already registered, an informative error message is rendered on the registration page while preserving entered form values.

## Depends on
- Step 01: Database Setup (`database/db.py`, `users` table schema, `get_db()`)

## Routes
- `GET /register` — Render the registration form template — Public access
- `POST /register` — Validate input, create user record in DB, set session, and redirect — Public access

## Database changes
No database schema changes.
(The `users` table schema with `id`, `name`, `email`, `password_hash`, and `created_at` columns was established in Step 01.)

New helper functions to add in `database/db.py`:
- `get_user_by_email(email)` — Check if a user with the specified email exists
- `create_user(name, email, password)` — Hash password and insert new user record into `users` table

## Templates
- **Create:** None (`templates/register.html` already exists)
- **Modify:** `templates/register.html` — Update form action to `url_for('register')`, display error alerts if validation fails, and retain submitted `name` and `email` input values upon error

## Files to change
- `app.py` — Handle `POST /register` route (form extraction, validation, calling DB helpers, session management, redirect)
- `database/db.py` — Add `get_user_by_email` and `create_user` helper functions
- `templates/register.html` — Support dynamic error message rendering and form value retention

## Files to create
- `.agents/specs/02-registration.md`

## New dependencies
No new dependencies (uses standard Flask features: `request`, `session`, `redirect`, `url_for`, `flash`, and `werkzeug.security`).

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug (`generate_password_hash`)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Never put DB logic directly in route functions — keep all database operations cleanly isolated inside `database/db.py`
- Normalize email input by stripping whitespace and converting to lowercase before checking uniqueness and storing
- Validate password length (minimum 8 characters)
- Do not return raw strings for implemented routes — always render templates or redirect

## Definition of done
- [ ] `GET /register` displays the registration page with form fields for Name, Email, and Password
- [ ] Submitting valid details creates a new user row in the `users` table with a werkzeug-hashed password
- [ ] Submitting an existing email shows a clear error message ("Email already registered")
- [ ] Submitting invalid inputs (empty fields or password under 8 characters) displays appropriate error messages
- [ ] On validation error, entered `name` and `email` remain populated in the form (password field cleared)
- [ ] Successful registration sets `session['user_id']` and redirects the user with a success flash message
- [ ] All database interactions use parameterized queries in `database/db.py`
- [ ] Automated tests or manual request testing confirm clean execution without errors

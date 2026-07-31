# Spec: Login and Logout

## Overview
Implements complete user authentication login and logout flows for Spendly. Existing users can sign into their accounts using their registered email and password. Credentials are securely verified against SQLite database user records using `werkzeug.security.check_password_hash`. Upon successful login, active user details (`user_id` and `user_name`) are stored in Flask's encrypted session, and a success flash message is displayed. Logging out cleanly clears the user session and redirects to the landing page.

## Depends on
- Step 01: Database Setup (`01-database-setup.md`)
- Step 02: Registration (`02-registration.md`)

## Routes
- `GET /login` — Renders login form — Public (redirects to `/` if user is already authenticated)
- `POST /login` — Processes credentials, sets session on success, or re-renders form with error — Public
- `GET /logout` — Clears Flask session, flashes logout notice, redirects to `/` — Logged-in / Public

## Database changes
No database changes.

## Templates
- **Create:** None
- **Modify:**
  - `templates/login.html`: Update form action to use `{{ url_for('login') }}`, handle pre-filled email value on error, and ensure accessibility.
  - `templates/base.html`: Ensure navigation header conditionally displays user name and Logout link when logged in, or Login/Register links when logged out. Ensure flashed messages are rendered.

## Files to change
- `app.py` — Implement `GET /login`, `POST /login`, and `GET /logout` handlers
- `database/db.py` — Ensure helper function `get_user_by_email` or password verification helper is available
- `templates/login.html` — Update login form markup and error state handling
- `templates/base.html` — Ensure dynamic navbar session handling and flash message display

## Files to create
- `tests/test_login_logout.py` — Unit and integration tests for login/logout functionality

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed and checked with werkzeug (`check_password_hash`)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Always use `url_for()` for template links and route redirects

## Definition of done
- [ ] `GET /login` displays login form when user is not authenticated
- [ ] `GET /login` redirects authenticated users to `/`
- [ ] Submitting empty fields on `POST /login` displays an error message "All fields are required."
- [ ] Submitting non-existent email address displays "Invalid email or password."
- [ ] Submitting incorrect password displays "Invalid email or password."
- [ ] Submitting valid credentials logs user in, sets `session['user_id']` and `session['user_name']`, flashes welcome message, and redirects to `/`
- [ ] Base template navigation reflects logged-in state (displays user greeting and Logout link)
- [ ] `GET /logout` clears `session`, flashes "You have been logged out.", and redirects to `/`
- [ ] All tests in `tests/test_login_logout.py` pass via `pytest`

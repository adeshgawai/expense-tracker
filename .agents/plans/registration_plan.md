# Implementation Plan — Step 2: User Registration

Implement user account registration for the Spendly expense tracker, connecting the `/register` frontend form to backend database operations and Flask session management.

---

## Goal Description
Enable new users to sign up for Spendly by submitting their full name, email address, and password via the `/register` form. The feature will validate inputs, enforce email uniqueness, securely hash passwords using `werkzeug.security.generate_password_hash`, insert user records into SQLite via parameterized queries, establish a logged-in user session (`session['user_id']`), and redirect to the application landing page. In case of validation errors (missing fields, weak password, duplicate email), the form re-renders with clear error feedback while preserving entered form values.

---

## User Review Required

> [!NOTE]
> **Flask Session Secret Key**: Session management (`session['user_id']`) requires `app.secret_key` to be configured in `app.py`. A standard secret key (e.g. `"spendly-dev-secret-key-2026"`) will be set.

> [!IMPORTANT]
> **Input Normalization & Security**:
> - Email addresses will be stripped of leading/trailing whitespace and converted to lowercase prior to database checks and insertions.
> - Passwords will strictly require a minimum length of 8 characters and will be securely hashed using Werkzeug (`generate_password_hash`).

---

## Open Questions

- None at present. All requirements and constraints are fully specified in `.agents/specs/02-registration.md`.

---

## Proposed Changes

### Database Layer

#### [MODIFY] `database/db.py`
Add database helper functions for checking email existence and inserting new user records cleanly without putting SQL logic in Flask routes:

1. `get_user_by_email(email)`:
   - Normalize email (`email.strip().lower()`).
   - Run parameterized query: `SELECT * FROM users WHERE LOWER(email) = ?;`
   - Return `sqlite3.Row` if found, else `None`.

2. `create_user(name, email, password)`:
   - Normalize inputs: `clean_name = name.strip()`, `clean_email = email.strip().lower()`.
   - Hash password: `password_hash = generate_password_hash(password)`.
   - Run parameterized query: `INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?);`
   - Commit transaction and return `cursor.lastrowid` (the created user's ID).

---

### Application Layer & Routes

#### [MODIFY] `app.py`
1. Configure `app.secret_key = "spendly-dev-secret-key-2026"` (or from environment).
2. Import `request`, `session`, `redirect`, `url_for`, `flash` from `flask`.
3. Import `get_user_by_email` and `create_user` from `database.db`.
4. Update the `/register` route to accept `methods=["GET", "POST"]`:
   - **For `GET` requests**:
     - Render `templates/register.html`.
   - **For `POST` requests**:
     - Extract `name = request.form.get("name", "").strip()`, `email = request.form.get("email", "").strip()`, `password = request.form.get("password", "")`.
     - Perform validation:
       1. **Missing fields**: If `not name` or `not email` or `not password`:
          - Render `register.html` with `error="All fields are required."`, passing `name` and `email`.
       2. **Password length**: If `len(password) < 8`:
          - Render `register.html` with `error="Password must be at least 8 characters long."`, passing `name` and `email`.
       3. **Duplicate email check**: Call `get_user_by_email(email)`. If existing user found:
          - Render `register.html` with `error="An account with this email address already exists."`, passing `name` and `email`.
     - **On Successful Validation**:
       - Call `user_id = create_user(name, email, password)`.
       - Set `session['user_id'] = user_id`.
       - Set `session['user_name'] = name`.
       - Flash success message: `"Welcome to Spendly, " + name + "! Your account has been created."`
       - Redirect to `url_for('landing')` (or `/`).

---

### Presentation Layer & Templates

#### [MODIFY] `templates/register.html`
1. Update `<form>` tag action to `action="{{ url_for('register') }}"` and `method="POST"`.
2. Update `<input id="name">` to preserve submitted value on validation error: `value="{{ name or '' }}"`.
3. Update `<input id="email">` to preserve submitted value on validation error: `value="{{ email or '' }}"`.
4. Leave password input empty (`value=""`) for security.
5. Verify error banner rendering block:
   ```html
   {% if error %}
   <div class="auth-error">{{ error }}</div>
   {% endif %}
   ```

---

## Verification Plan

### Automated Tests
Create a dedicated test file `tests/test_register.py` using `pytest` and `pytest-flask` client to verify:
1. **GET `/register`**:
   - Asserts HTTP 200 response and presence of registration form inputs.
2. **POST `/register` - Successful Registration**:
   - Submits valid name, unique email, and password (>= 8 chars).
   - Asserts HTTP 302 redirect to `/`.
   - Asserts user row exists in SQLite `users` table with matching email and hashed password.
   - Asserts `session['user_id']` is populated.
3. **POST `/register` - Duplicate Email Error**:
   - Attempts registration with `demo@spendly.com` (existing seeded user).
   - Asserts HTTP 200 response with error message `"An account with this email address already exists."`
   - Asserts form retains entered name and email.
4. **POST `/register` - Short Password Error**:
   - Submits password with length < 8 (e.g. `"123"`).
   - Asserts HTTP 200 response with error message `"Password must be at least 8 characters long."`
5. **POST `/register` - Missing Fields**:
   - Submits empty form fields.
   - Asserts HTTP 200 response with error message `"All fields are required."`

Run test suite:
```bash
pytest tests/test_register.py
```

### Manual Verification
1. Run application: `python app.py`.
2. Open browser at `http://127.0.0.1:5001/register`.
3. Test submitting invalid forms (short password, empty fields, existing email `demo@spendly.com`).
4. Test submitting valid new user details (e.g., `rahul.sharma@example.com`, password `password123`).
5. Confirm successful creation, session creation, and landing page redirection.

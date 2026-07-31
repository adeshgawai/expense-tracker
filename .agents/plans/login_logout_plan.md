# Implementation Plan - Step 03: Login and Logout

This plan details the implementation of user authentication (login and logout) for Spendly, building upon the database setup (Step 01) and registration feature (Step 02).

## Goal Description
Implement the `/login` (GET & POST) and `/logout` (GET) routes in `app.py`, update `login.html` and `base.html` templates for dynamic navigation state and flashed messages, and add automated pytest coverage in `tests/test_login_logout.py`.

## User Review Required
> [!NOTE]
> No database schema modifications are required for this step as `users` table was established in Step 01 and populated in Step 02. `werkzeug.security.check_password_hash` will be used for password verification.

## Proposed Changes

### Flask Application Layer (`app.py`)
#### [MODIFY] [`app.py`](file:///E:/Agentic%20AI/Agentic%20coding/expense-tracker/app.py)
- Import `check_password_hash` from `werkzeug.security`.
- Update `/login` GET handler to redirect logged-in users (`session.get("user_id")`) to `landing`.
- Implement `/login` POST handler:
  - Extract and sanitize `email` and `password`.
  - Validate required fields (return error `"All fields are required."`).
  - Retrieve user using `get_user_by_email(email)`.
  - Check password using `check_password_hash`. Return error `"Invalid email or password."` if email or password mismatch.
  - Set `session["user_id"]` and `session["user_name"]`.
  - Flash `"Welcome back, <name>!"` and redirect to `landing`.
- Implement `/logout` GET handler:
  - Clear `session`.
  - Flash `"You have been logged out."`.
  - Redirect to `landing`.

```python
from werkzeug.security import check_password_hash

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id") and request.method == "GET":
        return redirect(url_for("landing"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:
            return render_template("login.html", error="All fields are required.", email=email)

        user = get_user_by_email(email)
        if not user or not check_password_hash(user["password_hash"], password):
            return render_template("login.html", error="Invalid email or password.", email=email)

        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        flash(f"Welcome back, {user['name']}!", "success")
        return redirect(url_for("landing"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("landing"))
```

---

### Template Layer (`templates/`)
#### [MODIFY] [`templates/login.html`](file:///E:/Agentic%20AI/Agentic%20coding/expense-tracker/templates/login.html)
- Update `<form method="POST" action="/login">` to `<form method="POST" action="{{ url_for('login') }}">`.
- Retain entered email value on validation errors: `value="{{ email or '' }}"`.

#### [MODIFY] [`templates/base.html`](file:///E:/Agentic%20AI/Agentic%20coding/expense-tracker/templates/base.html)
- Add flash message container inside `<main class="main-content">` to display alert messages.
- Update top navigation `.nav-links`:
  - If `session.get('user_id')`: Display user greeting, link to Profile (`url_for('profile')`), and Logout button (`url_for('logout')`).
  - Else: Display Sign in (`url_for('login')`) and Get started CTA (`url_for('register')`).

---

### Test Suite (`tests/`)
#### [NEW] [`tests/test_login_logout.py`](file:///E:/Agentic%20AI/Agentic%20coding/expense-tracker/tests/test_login_logout.py)
Create tests covering:
- `test_login_page_get_unauthenticated`
- `test_login_page_get_authenticated_redirects`
- `test_login_missing_fields`
- `test_login_nonexistent_email`
- `test_login_incorrect_password`
- `test_login_success`
- `test_logout_clears_session`

## Verification Plan

### Automated Tests
Run `pytest` to execute all test suites (including existing `test_register.py` and new `test_login_logout.py`).

```bash
pytest
```

### Manual Verification
1. Open browser at `http://127.0.0.1:5001/login`.
2. Attempt login with invalid credentials to verify error feedback and field retention.
3. Login with `demo@spendly.com` / `demo123`.
4. Verify dynamic navbar updates to show user session and profile/logout options.
5. Click Logout and verify session termination and flash message display.

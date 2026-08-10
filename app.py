import os
from datetime import datetime
from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from database.db import (
    create_expense,
    create_user,
    get_user_by_email,
    get_user_by_id,
    get_user_category_expenses,
    get_user_profile_stats,
    get_user_recent_transactions,
    init_db,
    seed_db,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "spendly-dev-secret-key-2026")

# Initialize database tables and seed sample data
with app.app_context():
    init_db()
    seed_db()


def is_valid_date(date_str):
    """Validates if a string is a valid YYYY-MM-DD date."""
    if not date_str:
        return False
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id") and request.method == "GET":
        return redirect(url_for("profile"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not name or not email or not password:
            return render_template(
                "register.html",
                error="All fields are required.",
                name=name,
                email=email,
            )

        if len(password) < 8:
            return render_template(
                "register.html",
                error="Password must be at least 8 characters long.",
                name=name,
                email=email,
            )

        if get_user_by_email(email):
            return render_template(
                "register.html",
                error="An account with this email address already exists.",
                name=name,
                email=email,
            )

        user_id = create_user(name, email, password)
        session["user_id"] = user_id
        session["user_name"] = name
        flash(f"Welcome to Spendly, {name}! Your account has been created successfully.", "success")
        return redirect(url_for("profile"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id") and request.method == "GET":
        return redirect(url_for("profile"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:
            return render_template(
                "login.html",
                error="All fields are required.",
                email=email,
            )

        user = get_user_by_email(email)
        if not user or not check_password_hash(user["password_hash"], password):
            return render_template(
                "login.html",
                error="Invalid email or password.",
                email=email,
            )

        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        flash(f"Welcome back, {user['name']}!", "success")
        return redirect(url_for("profile"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("landing"))


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


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

    raw_start = request.args.get("start_date", "").strip()
    raw_end = request.args.get("end_date", "").strip()

    start_date = raw_start if is_valid_date(raw_start) else None
    end_date = raw_end if is_valid_date(raw_end) else None

    if raw_start and not start_date:
        flash("Invalid start date format. Please use YYYY-MM-DD.", "warning")
    if raw_end and not end_date:
        flash("Invalid end date format. Please use YYYY-MM-DD.", "warning")

    if start_date and end_date and start_date > end_date:
        start_date, end_date = end_date, start_date
        flash("Start date was after end date. Range was automatically adjusted.", "info")

    limit = 50 if (start_date or end_date) else 10
    stats = get_user_profile_stats(user_id, start_date=start_date, end_date=end_date)
    category_expenses = get_user_category_expenses(user_id, start_date=start_date, end_date=end_date)
    recent_transactions = get_user_recent_transactions(user_id, limit=limit, start_date=start_date, end_date=end_date)

    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        category_expenses=category_expenses,
        recent_transactions=recent_transactions,
        start_date=start_date or "",
        end_date=end_date or "",
    )


@app.route("/analytics", methods=["GET", "POST"])
def analytics():
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in to access analytics.", "warning")
        return redirect(url_for("login"))

    user = get_user_by_id(user_id)
    if not user:
        session.clear()
        flash("User account not found. Please log in again.", "warning")
        return redirect(url_for("login"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        if email:
            flash("Thank you! We'll notify you as soon as Spendly Analytics launches.", "success")
        return redirect(url_for("analytics"))

    return render_template("analytics.html", user=user)



ALLOWED_CATEGORIES = [
    "Food",
    "Transport",
    "Bills",
    "Health",
    "Entertainment",
    "Shopping",
    "Other",
]


@app.route("/expenses/add", methods=["GET", "POST"])
def add_expense():
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in to add an expense.", "warning")
        return redirect(url_for("login"))

    today_str = datetime.now().strftime("%Y-%m-%d")

    if request.method == "POST":
        amount_raw = request.form.get("amount", "").strip()
        category = request.form.get("category", "").strip()
        date_raw = request.form.get("date", "").strip()
        description = request.form.get("description", "").strip()

        # Validation: required fields
        if not amount_raw or not category or not date_raw:
            return render_template(
                "add_expense.html",
                error="Amount, Category, and Date are required.",
                amount=amount_raw,
                category=category,
                date=date_raw or today_str,
                description=description,
                categories=ALLOWED_CATEGORIES,
            )

        # Validation: positive numeric amount
        try:
            amount = float(amount_raw)
            if amount <= 0:
                raise ValueError("Amount must be positive.")
        except ValueError:
            return render_template(
                "add_expense.html",
                error="Please enter a valid positive amount.",
                amount=amount_raw,
                category=category,
                date=date_raw,
                description=description,
                categories=ALLOWED_CATEGORIES,
            )

        # Validation: category must be in allowed categories
        if category not in ALLOWED_CATEGORIES:
            return render_template(
                "add_expense.html",
                error="Please select a valid expense category.",
                amount=amount_raw,
                category=category,
                date=date_raw,
                description=description,
                categories=ALLOWED_CATEGORIES,
            )

        # Validation: date must be valid YYYY-MM-DD
        if not is_valid_date(date_raw):
            return render_template(
                "add_expense.html",
                error="Please enter a valid date in YYYY-MM-DD format.",
                amount=amount_raw,
                category=category,
                date=date_raw,
                description=description,
                categories=ALLOWED_CATEGORIES,
            )

        create_expense(
            user_id=user_id,
            amount=amount,
            category=category,
            date=date_raw,
            description=description,
        )
        flash("Expense added successfully!", "success")
        return redirect(url_for("profile"))

    return render_template(
        "add_expense.html",
        date=today_str,
        categories=ALLOWED_CATEGORIES,
    )


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)

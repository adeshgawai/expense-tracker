import os
from flask import Flask, flash, redirect, render_template, request, session, url_for

from werkzeug.security import check_password_hash

from database.db import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    get_user_category_expenses,
    get_user_profile_stats,
    init_db,
    seed_db,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "spendly-dev-secret-key-2026")

# Initialize database tables and seed sample data
with app.app_context():
    init_db()
    seed_db()


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

    stats = get_user_profile_stats(user_id)
    category_expenses = get_user_category_expenses(user_id)
    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        category_expenses=category_expenses,
    )


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)


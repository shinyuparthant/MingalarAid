import os
import sqlite3
from functools import wraps
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, "mingalar_aid.db")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-development-secret")


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS disasters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            disaster_date TEXT NOT NULL,
            place TEXT NOT NULL,
            description TEXT NOT NULL,
            evidence_url TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            submitted_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS donations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            disaster_id INTEGER,
            donor_name TEXT NOT NULL,
            donation_type TEXT NOT NULL,
            amount_or_items TEXT NOT NULL,
            contact TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(disaster_id) REFERENCES disasters(id)
        );

        CREATE TABLE IF NOT EXISTS volunteers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            disaster_id INTEGER,
            volunteer_name TEXT NOT NULL,
            skills TEXT NOT NULL,
            contact TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(disaster_id) REFERENCES disasters(id)
        );

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user'
        );
        """)

        donation_columns = {
            row["name"] for row in db.execute("PRAGMA table_info(donations)").fetchall()
        }
        if "payment_method" not in donation_columns:
            db.execute("ALTER TABLE donations ADD COLUMN payment_method TEXT")
        if "amount" not in donation_columns:
            db.execute("ALTER TABLE donations ADD COLUMN amount INTEGER")
        if "currency" not in donation_columns:
            db.execute("ALTER TABLE donations ADD COLUMN currency TEXT NOT NULL DEFAULT 'MMK'")
        if "status" not in donation_columns:
            db.execute("ALTER TABLE donations ADD COLUMN status TEXT NOT NULL DEFAULT 'pending'")

        for username, password, role in (
            ("admin", "admin@123", "admin"),
            ("user", "user@123", "user"),
        ):
            db.execute(
                "INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, generate_password_hash(password), role),
            )

        approved = db.execute(
            "SELECT id FROM disasters WHERE place = ? AND description = ?",
            ("Sample River Township", "Example flood report for demonstrating the Mingalar Aid workflow."),
        ).fetchone()
        if approved is None:
            cursor = db.execute(
                """INSERT INTO disasters
                   (disaster_date, place, description, evidence_url, status, submitted_at)
                   VALUES (?, ?, ?, ?, 'approved', ?)""",
                (
                    "2026-11-01",
                    "Sample River Township",
                    "Example flood report for demonstrating the Mingalar Aid workflow.",
                    "",
                    datetime.utcnow().isoformat(timespec="seconds"),
                ),
            )
            approved_id = cursor.lastrowid
        else:
            approved_id = approved["id"]

        if db.execute("SELECT 1 FROM donations WHERE donor_name = ?", ("Example Donor",)).fetchone() is None:
            db.execute(
                """INSERT INTO donations
                   (disaster_id, donor_name, donation_type, amount_or_items, contact, created_at,
                    payment_method, amount, currency, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'MMK', 'approved')""",
                (
                    approved_id,
                    "Example Donor",
                    "KBZPay",
                    "50,000 MMK",
                    "example-donor@example.com",
                    datetime.utcnow().isoformat(timespec="seconds"),
                    "KBZPay",
                    50000,
                ),
            )
        else:
            db.execute(
                """UPDATE donations
                   SET donation_type = 'KBZPay', amount_or_items = '50,000 MMK',
                       payment_method = 'KBZPay', amount = 50000, currency = 'MMK'
                       , status = 'approved'
                   WHERE donor_name = 'Example Donor'"""
            )

        if db.execute("SELECT 1 FROM volunteers WHERE volunteer_name = ?", ("Example Volunteer",)).fetchone() is None:
            db.execute(
                """INSERT INTO volunteers
                   (disaster_id, volunteer_name, skills, contact, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    approved_id,
                    "Example Volunteer",
                    "Packing supplies and local transportation",
                    "example-volunteer@example.com",
                    datetime.utcnow().isoformat(timespec="seconds"),
                ),
            )


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Please sign in as an administrator first.", "error")
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)
    return wrapped


def user_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in to continue.", "error")
            return redirect(url_for("user_login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


@app.route("/")
def index():
    with get_db() as db:
        disasters = db.execute(
            "SELECT * FROM disasters WHERE status = 'approved' ORDER BY disaster_date DESC, id DESC LIMIT 6"
        ).fetchall()
    return render_template("index.html", disasters=disasters)


@app.route("/disasters")
def disasters():
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM disasters WHERE status = 'approved' ORDER BY disaster_date DESC, id DESC"
        ).fetchall()
    return render_template("disasters.html", disasters=rows)


@app.route("/disasters/<int:disaster_id>")
def disaster_detail(disaster_id):
    with get_db() as db:
        disaster = db.execute(
            "SELECT * FROM disasters WHERE id = ? AND status = 'approved'", (disaster_id,)
        ).fetchone()
    if disaster is None:
        abort(404)
    return render_template("disaster_detail.html", disaster=disaster)


@app.route("/report", methods=["GET", "POST"])
@user_required
def report_disaster():
    if request.method == "POST":
        disaster_date = request.form.get("disaster_date", "").strip()
        place = request.form.get("place", "").strip()
        description = request.form.get("description", "").strip()
        evidence_url = request.form.get("evidence_url", "").strip()

        if not disaster_date or not place or not description:
            flash("Please complete the date, location, and description.", "error")
            return render_template("report.html")

        with get_db() as db:
            db.execute(
                """INSERT INTO disasters
                   (disaster_date, place, description, evidence_url, status, submitted_at)
                   VALUES (?, ?, ?, ?, 'pending', ?)""",
                (disaster_date, place, description, evidence_url, datetime.utcnow().isoformat(timespec="seconds"))
            )
        flash("Your report was submitted for administrator review. Thank you.", "success")
        return redirect(url_for("report"))
    return render_template("report.html")


@app.route("/donate", methods=["GET", "POST"])
@user_required
def donate():
    with get_db() as db:
        approved = db.execute(
            "SELECT id, place, disaster_date FROM disasters WHERE status = 'approved' ORDER BY disaster_date DESC"
        ).fetchall()

    if request.method == "POST":
        name = request.form.get("donor_name", "").strip()
        payment_method = request.form.get("payment_method", "").strip()
        amount_text = request.form.get("amount", "").strip()
        contact = request.form.get("contact", "").strip()
        disaster_id = request.form.get("disaster_id") or None

        try:
            amount = int(amount_text)
        except ValueError:
            amount = 0

        if not name or payment_method not in ("KBZPay", "WavePay") or amount <= 0 or not contact:
            flash("Please complete all required fields.", "error")
            return render_template("donate.html", disasters=approved)

        if disaster_id:
            with get_db() as db:
                valid_disaster = db.execute(
                    "SELECT 1 FROM disasters WHERE id = ? AND status = 'approved'", (disaster_id,)
                ).fetchone()
            if valid_disaster is None:
                flash("Please choose a valid approved disaster.", "error")
                return render_template("donate.html", disasters=approved)

        with get_db() as db:
            db.execute(
                """INSERT INTO donations
                   (disaster_id, donor_name, donation_type, amount_or_items, contact, created_at,
                    payment_method, amount, currency, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'MMK', 'pending')""",
                (
                    disaster_id,
                    name,
                    payment_method,
                    f"{amount:,} MMK",
                    contact,
                    datetime.utcnow().isoformat(timespec="seconds"),
                    payment_method,
                    amount,
                )
            )
        flash("Thank you! Your donation is waiting for administrator confirmation.", "success")
        return redirect(url_for("donate"))
    return render_template("donate.html", disasters=approved)


@app.route("/donations")
def public_donations():
    with get_db() as db:
        donations = db.execute(
            """SELECT donations.donor_name,
                      donations.donation_type,
                      donations.amount_or_items,
                      donations.payment_method,
                      donations.amount,
                      donations.currency,
                      donations.created_at,
                      disasters.id AS disaster_id,
                      disasters.place AS disaster_place
               FROM donations
               LEFT JOIN disasters ON disasters.id = donations.disaster_id
               WHERE donations.status = 'approved'
                 AND (donations.disaster_id IS NULL OR disasters.status = 'approved')
               ORDER BY donations.created_at DESC, donations.id DESC"""
        ).fetchall()
    return render_template("donations.html", donations=donations)


@app.route("/volunteer", methods=["GET", "POST"])
@user_required
def volunteer():
    with get_db() as db:
        approved = db.execute(
            "SELECT id, place, disaster_date FROM disasters WHERE status = 'approved' ORDER BY disaster_date DESC"
        ).fetchall()

    if request.method == "POST":
        name = request.form.get("volunteer_name", "").strip()
        skills = request.form.get("skills", "").strip()
        contact = request.form.get("contact", "").strip()
        disaster_id = request.form.get("disaster_id") or None

        if not all([name, skills, contact]):
            flash("Please complete all required fields.", "error")
            return render_template("volunteer.html", disasters=approved)

        with get_db() as db:
            db.execute(
                """INSERT INTO volunteers
                   (disaster_id, volunteer_name, skills, contact, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (disaster_id, name, skills, contact, datetime.utcnow().isoformat(timespec="seconds"))
            )
        flash("Thank you for offering to volunteer. An organizer can contact you.", "success")
        return redirect(url_for("volunteer"))
    return render_template("volunteer.html", disasters=approved)


@app.route("/volunteers")
def public_volunteers():
    with get_db() as db:
        volunteers = db.execute(
            """SELECT volunteers.volunteer_name,
                      volunteers.skills,
                      volunteers.created_at,
                      disasters.id AS disaster_id,
                      disasters.place AS disaster_place
               FROM volunteers
               LEFT JOIN disasters ON disasters.id = volunteers.disaster_id
               WHERE volunteers.disaster_id IS NULL OR disasters.status = 'approved'
               ORDER BY volunteers.created_at DESC, volunteers.id DESC"""
        ).fetchall()
    return render_template("volunteers.html", volunteers=volunteers)


@app.route("/login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        with get_db() as db:
            user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            flash("You are signed in.", "success")
            next_url = request.args.get("next", "")
            if next_url.startswith("/") and not next_url.startswith("//"):
                return redirect(next_url)
            return redirect(url_for("index"))
        flash("Incorrect username or password.", "error")
    return render_template("user_login.html")


@app.route("/logout")
def user_logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("index"))


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        with get_db() as db:
            user = db.execute(
                "SELECT * FROM users WHERE username = ? AND role = 'admin'", (username,)
            ).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            flash("You are signed in.", "success")
            return redirect(url_for("admin_dashboard"))
        flash("Incorrect username or password.", "error")
    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("index"))


@app.route("/admin")
@admin_required
def admin_dashboard():
    selected_date = request.args.get("date", "").strip()
    selected_month = request.args.get("month", "").strip()
    selected_year = request.args.get("year", "").strip()
    selected_disaster = request.args.get("disaster_id", "").strip()

    donation_filters = []
    donation_params = []
    if selected_date:
        donation_filters.append("date(donations.created_at) = ?")
        donation_params.append(selected_date)
    elif selected_month:
        donation_filters.append("substr(donations.created_at, 1, 7) = ?")
        donation_params.append(selected_month)
    elif selected_year:
        donation_filters.append("substr(donations.created_at, 1, 4) = ?")
        donation_params.append(selected_year)
    if selected_disaster:
        if selected_disaster == "general":
            donation_filters.append("donations.disaster_id IS NULL")
        elif selected_disaster.isdigit():
            donation_filters.append("donations.disaster_id = ?")
            donation_params.append(selected_disaster)

    donation_where = ""
    if donation_filters:
        donation_where = " WHERE " + " AND ".join(donation_filters)

    with get_db() as db:
        pending = db.execute("SELECT * FROM disasters WHERE status = 'pending' ORDER BY submitted_at DESC").fetchall()
        all_disasters = db.execute("SELECT * FROM disasters ORDER BY submitted_at DESC").fetchall()
        donations = db.execute(
            """SELECT donations.*, disasters.place AS disaster_place
               FROM donations
               LEFT JOIN disasters ON disasters.id = donations.disaster_id"""
            + donation_where
            + " ORDER BY donations.created_at DESC",
            donation_params,
        ).fetchall()
        total_donations = db.execute(
            "SELECT COALESCE(SUM(donations.amount), 0) AS total FROM donations"
            + (donation_where + " AND donations.status = 'approved'" if donation_where else " WHERE donations.status = 'approved'"),
            donation_params,
        ).fetchone()["total"]
        disaster_options = db.execute(
            "SELECT id, place, disaster_date FROM disasters ORDER BY disaster_date DESC, id DESC"
        ).fetchall()
        volunteers = db.execute("SELECT * FROM volunteers ORDER BY created_at DESC").fetchall()
    return render_template(
        "admin_dashboard.html",
        pending=pending,
        all_disasters=all_disasters,
        donations=donations,
        total_donations=total_donations,
        disaster_options=disaster_options,
        selected_date=selected_date,
        selected_month=selected_month,
        selected_year=selected_year,
        selected_disaster=selected_disaster,
        volunteers=volunteers
    )


@app.route("/admin/disasters/<int:disaster_id>/<action>", methods=["POST"])
@admin_required
def moderate_disaster(disaster_id, action):
    if action not in ("approve", "reject"):
        abort(404)
    status = "approved" if action == "approve" else "rejected"
    with get_db() as db:
        result = db.execute("UPDATE disasters SET status = ? WHERE id = ?", (status, disaster_id))
        if result.rowcount == 0:
            abort(404)
    flash(f"Report {status}.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/donations/<int:donation_id>/<action>", methods=["POST"])
@admin_required
def moderate_donation(donation_id, action):
    if action not in ("approve", "reject"):
        abort(404)
    status = "approved" if action == "approve" else "rejected"
    with get_db() as db:
        result = db.execute("UPDATE donations SET status = ? WHERE id = ?", (status, donation_id))
        if result.rowcount == 0:
            abort(404)
    flash(f"Donation {status}.", "success")
    return redirect(request.referrer or url_for("admin_dashboard"))


@app.errorhandler(404)
def not_found(_error):
    return render_template("404.html"), 404


init_db()

if __name__ == "__main__":
    app.run(debug=True)

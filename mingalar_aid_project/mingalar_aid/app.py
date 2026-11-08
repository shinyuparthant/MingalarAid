import os
import sqlite3
from functools import wraps
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, "mingalar_aid.db")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-development-secret")
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "change-me-now")


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
        """)


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            flash("Please sign in as an administrator first.", "error")
            return redirect(url_for("admin_login"))
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
def donate():
    with get_db() as db:
        approved = db.execute(
            "SELECT id, place, disaster_date FROM disasters WHERE status = 'approved' ORDER BY disaster_date DESC"
        ).fetchall()

    if request.method == "POST":
        name = request.form.get("donor_name", "").strip()
        donation_type = request.form.get("donation_type", "").strip()
        amount_or_items = request.form.get("amount_or_items", "").strip()
        contact = request.form.get("contact", "").strip()
        disaster_id = request.form.get("disaster_id") or None

        if not all([name, donation_type, amount_or_items, contact]):
            flash("Please complete all required fields.", "error")
            return render_template("donate.html", disasters=approved)

        with get_db() as db:
            db.execute(
                """INSERT INTO donations
                   (disaster_id, donor_name, donation_type, amount_or_items, contact, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (disaster_id, name, donation_type, amount_or_items, contact, datetime.utcnow().isoformat(timespec="seconds"))
            )
        flash("Thank you! Your donation offer has been recorded. An organizer can contact you.", "success")
        return redirect(url_for("donate"))
    return render_template("donate.html", disasters=approved)


@app.route("/volunteer", methods=["GET", "POST"])
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


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["is_admin"] = True
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
    with get_db() as db:
        pending = db.execute("SELECT * FROM disasters WHERE status = 'pending' ORDER BY submitted_at DESC").fetchall()
        all_disasters = db.execute("SELECT * FROM disasters ORDER BY submitted_at DESC").fetchall()
        donations = db.execute("SELECT * FROM donations ORDER BY created_at DESC").fetchall()
        volunteers = db.execute("SELECT * FROM volunteers ORDER BY created_at DESC").fetchall()
    return render_template(
        "admin_dashboard.html",
        pending=pending,
        all_disasters=all_disasters,
        donations=donations,
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


@app.errorhandler(404)
def not_found(_error):
    return render_template("404.html"), 404


init_db()

if __name__ == "__main__":
    app.run(debug=True)

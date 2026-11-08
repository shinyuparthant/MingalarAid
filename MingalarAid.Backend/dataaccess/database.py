import sqlite3
from datetime import datetime

from werkzeug.security import generate_password_hash

from config import DATABASE_PATH


def get_connection():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_connection() as db:
        db.executescript(
            """
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
                payment_method TEXT,
                amount INTEGER,
                currency TEXT NOT NULL DEFAULT 'MMK',
                status TEXT NOT NULL DEFAULT 'pending',
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
            """
        )

        columns = {row["name"] for row in db.execute("PRAGMA table_info(donations)")}
        migrations = {
            "payment_method": "ALTER TABLE donations ADD COLUMN payment_method TEXT",
            "amount": "ALTER TABLE donations ADD COLUMN amount INTEGER",
            "currency": "ALTER TABLE donations ADD COLUMN currency TEXT NOT NULL DEFAULT 'MMK'",
            "status": "ALTER TABLE donations ADD COLUMN status TEXT NOT NULL DEFAULT 'pending'",
        }
        for column, statement in migrations.items():
            if column not in columns:
                db.execute(statement)

        _seed_users(db)
        _seed_example_data(db)


def _seed_users(db):
    for username, password, role in (
        ("admin", "admin@123", "admin"),
        ("user", "user@123", "user"),
    ):
        db.execute(
            "INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (username, generate_password_hash(password), role),
        )


def _seed_example_data(db):
    description = "Example flood report for demonstrating the Mingalar Aid workflow."
    approved = db.execute(
        "SELECT id FROM disasters WHERE place = ? AND description = ?",
        ("Sample River Township", description),
    ).fetchone()
    if approved is None:
        cursor = db.execute(
            """INSERT INTO disasters
               (disaster_date, place, description, evidence_url, status, submitted_at)
               VALUES (?, ?, ?, '', 'approved', ?)""",
            ("2026-11-01", "Sample River Township", description, _now()),
        )
        disaster_id = cursor.lastrowid
    else:
        disaster_id = approved["id"]

    donation = db.execute(
        "SELECT id FROM donations WHERE donor_name = 'Example Donor'"
    ).fetchone()
    if donation is None:
        db.execute(
            """INSERT INTO donations
               (disaster_id, donor_name, donation_type, amount_or_items, contact,
                created_at, payment_method, amount, currency, status)
               VALUES (?, 'Example Donor', 'KBZPay', '50,000 MMK',
                       'example-donor@example.com', ?, 'KBZPay', 50000, 'MMK', 'approved')""",
            (disaster_id, _now()),
        )
    else:
        db.execute(
            """UPDATE donations
               SET donation_type = 'KBZPay', amount_or_items = '50,000 MMK',
                   payment_method = 'KBZPay', amount = 50000,
                   currency = 'MMK', status = 'approved'
               WHERE id = ?""",
            (donation["id"],),
        )

    volunteer = db.execute(
        "SELECT id FROM volunteers WHERE volunteer_name = 'Example Volunteer'"
    ).fetchone()
    if volunteer is None:
        db.execute(
            """INSERT INTO volunteers
               (disaster_id, volunteer_name, skills, contact, created_at)
               VALUES (?, 'Example Volunteer', 'Packing supplies and local transportation',
                       'example-volunteer@example.com', ?)""",
            (disaster_id, _now()),
        )


def _now():
    return datetime.utcnow().isoformat(timespec="seconds")

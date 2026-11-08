from datetime import datetime

from dataaccess.database import get_connection


def list_approved(limit=None):
    query = "SELECT * FROM disasters WHERE status = 'approved' ORDER BY disaster_date DESC, id DESC"
    if limit:
        query += " LIMIT ?"
        params = (limit,)
    else:
        params = ()
    with get_connection() as db:
        return db.execute(query, params).fetchall()


def list_approved_options():
    with get_connection() as db:
        return db.execute(
            "SELECT id, place, disaster_date FROM disasters WHERE status = 'approved' ORDER BY disaster_date DESC"
        ).fetchall()


def find_approved(disaster_id):
    with get_connection() as db:
        return db.execute(
            "SELECT * FROM disasters WHERE id = ? AND status = 'approved'", (disaster_id,)
        ).fetchone()


def create_report(disaster_date, place, description, evidence_url):
    with get_connection() as db:
        db.execute(
            """INSERT INTO disasters
               (disaster_date, place, description, evidence_url, status, submitted_at)
               VALUES (?, ?, ?, ?, 'pending', ?)""",
            (disaster_date, place, description, evidence_url, datetime.utcnow().isoformat(timespec="seconds")),
        )


def admin_snapshot():
    with get_connection() as db:
        pending = db.execute(
            "SELECT * FROM disasters WHERE status = 'pending' ORDER BY submitted_at DESC"
        ).fetchall()
        all_disasters = db.execute(
            "SELECT * FROM disasters ORDER BY submitted_at DESC"
        ).fetchall()
        options = db.execute(
            "SELECT id, place, disaster_date FROM disasters ORDER BY disaster_date DESC, id DESC"
        ).fetchall()
    return pending, all_disasters, options


def update_status(disaster_id, status):
    with get_connection() as db:
        result = db.execute(
            "UPDATE disasters SET status = ? WHERE id = ?", (status, disaster_id)
        )
        return result.rowcount > 0

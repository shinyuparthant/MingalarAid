from datetime import datetime

from dataaccess.database import get_connection


def create(disaster_id, name, skills, contact):
    with get_connection() as db:
        db.execute(
            """INSERT INTO volunteers
               (disaster_id, volunteer_name, skills, contact, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (disaster_id, name, skills, contact, datetime.utcnow().isoformat(timespec="seconds")),
        )


def list_public():
    with get_connection() as db:
        return db.execute(
            """SELECT volunteers.volunteer_name, volunteers.skills, volunteers.created_at,
                      disasters.id AS disaster_id, disasters.place AS disaster_place
               FROM volunteers
               LEFT JOIN disasters ON disasters.id = volunteers.disaster_id
               WHERE volunteers.disaster_id IS NULL OR disasters.status = 'approved'
               ORDER BY volunteers.created_at DESC, volunteers.id DESC"""
        ).fetchall()


def list_all():
    with get_connection() as db:
        return db.execute(
            "SELECT * FROM volunteers ORDER BY created_at DESC"
        ).fetchall()

from datetime import datetime

from dataaccess.database import get_connection


def create(disaster_id, donor_name, payment_method, amount, contact):
    with get_connection() as db:
        db.execute(
            """INSERT INTO donations
               (disaster_id, donor_name, donation_type, amount_or_items, contact,
                created_at, payment_method, amount, currency, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'MMK', 'pending')""",
            (
                disaster_id,
                donor_name,
                payment_method,
                f"{amount:,} MMK",
                contact,
                datetime.utcnow().isoformat(timespec="seconds"),
                payment_method,
                amount,
            ),
        )


def list_public():
    with get_connection() as db:
        return db.execute(
            """SELECT donations.donor_name, donations.donation_type,
                      donations.amount_or_items, donations.payment_method,
                      donations.amount, donations.currency, donations.created_at,
                      disasters.id AS disaster_id, disasters.place AS disaster_place
               FROM donations
               LEFT JOIN disasters ON disasters.id = donations.disaster_id
               WHERE donations.status = 'approved'
                 AND (donations.disaster_id IS NULL OR disasters.status = 'approved')
               ORDER BY donations.created_at DESC, donations.id DESC"""
        ).fetchall()


def admin_report(filters):
    clauses = []
    params = []
    if filters["date"]:
        clauses.append("date(donations.created_at) = ?")
        params.append(filters["date"])
    elif filters["month"]:
        clauses.append("substr(donations.created_at, 1, 7) = ?")
        params.append(filters["month"])
    elif filters["year"]:
        clauses.append("substr(donations.created_at, 1, 4) = ?")
        params.append(filters["year"])

    selected_disaster = filters["disaster_id"]
    if selected_disaster == "general":
        clauses.append("donations.disaster_id IS NULL")
    elif selected_disaster.isdigit():
        clauses.append("donations.disaster_id = ?")
        params.append(selected_disaster)

    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    approved_where = (
        where + " AND donations.status = 'approved'"
        if where
        else " WHERE donations.status = 'approved'"
    )

    with get_connection() as db:
        donations = db.execute(
            """SELECT donations.*, disasters.place AS disaster_place
               FROM donations
               LEFT JOIN disasters ON disasters.id = donations.disaster_id"""
            + where
            + " ORDER BY donations.created_at DESC",
            params,
        ).fetchall()
        total = db.execute(
            "SELECT COALESCE(SUM(donations.amount), 0) AS total FROM donations" + approved_where,
            params,
        ).fetchone()["total"]
    return donations, total


def update_status(donation_id, status):
    with get_connection() as db:
        result = db.execute(
            "UPDATE donations SET status = ? WHERE id = ?", (status, donation_id)
        )
        return result.rowcount > 0

from dataaccess.database import get_connection


def dashboard_summary():
    with get_connection() as db:
        return {
            "pending_reports": db.execute(
                "SELECT COUNT(*) FROM disasters WHERE status = 'pending'"
            ).fetchone()[0],
            "total_reports": db.execute("SELECT COUNT(*) FROM disasters").fetchone()[0],
            "pending_donations": db.execute(
                "SELECT COUNT(*) FROM donations WHERE status = 'pending'"
            ).fetchone()[0],
            "confirmed_total": db.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM donations WHERE status = 'approved'"
            ).fetchone()[0],
            "volunteers": db.execute("SELECT COUNT(*) FROM volunteers").fetchone()[0],
        }

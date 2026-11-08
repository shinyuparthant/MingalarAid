from dataaccess.database import get_connection


def find_by_username(username, role=None):
    query = "SELECT * FROM users WHERE username = ?"
    params = [username]
    if role:
        query += " AND role = ?"
        params.append(role)
    with get_connection() as db:
        return db.execute(query, params).fetchone()

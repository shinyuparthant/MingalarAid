from dataaccess import disaster_repository


def latest(limit=6):
    return disaster_repository.list_approved(limit)


def list_public():
    return disaster_repository.list_approved()


def get_public(disaster_id):
    return disaster_repository.find_approved(disaster_id)


def approved_options():
    return disaster_repository.list_approved_options()


def submit_report(form):
    disaster_date = form.get("disaster_date", "").strip()
    place = form.get("place", "").strip()
    description = form.get("description", "").strip()
    evidence_url = form.get("evidence_url", "").strip()
    if not disaster_date or not place or not description:
        return False, "Please complete the date, location, and description."
    disaster_repository.create_report(disaster_date, place, description, evidence_url)
    return True, None


def admin_snapshot():
    return disaster_repository.admin_snapshot()


def moderate(disaster_id, action):
    if action not in ("approve", "reject"):
        return None
    status = "approved" if action == "approve" else "rejected"
    return status if disaster_repository.update_status(disaster_id, status) else None

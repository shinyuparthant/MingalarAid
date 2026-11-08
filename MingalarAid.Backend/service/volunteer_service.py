from dataaccess import disaster_repository, volunteer_repository


def submit(form):
    name = form.get("volunteer_name", "").strip()
    skills = form.get("skills", "").strip()
    contact = form.get("contact", "").strip()
    disaster_id = form.get("disaster_id") or None
    if not name or not skills or not contact:
        return False, "Please complete all required fields."
    if disaster_id and disaster_repository.find_approved(disaster_id) is None:
        return False, "Please choose a valid approved disaster."
    volunteer_repository.create(disaster_id, name, skills, contact)
    return True, None


def list_public():
    return volunteer_repository.list_public()


def list_all():
    return volunteer_repository.list_all()

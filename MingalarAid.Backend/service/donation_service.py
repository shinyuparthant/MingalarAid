from dataaccess import disaster_repository, donation_repository

PAYMENT_METHODS = ("KBZPay", "WavePay")


def submit(form):
    donor_name = form.get("donor_name", "").strip()
    payment_method = form.get("payment_method", "").strip()
    contact = form.get("contact", "").strip()
    disaster_id = form.get("disaster_id") or None
    try:
        amount = int(form.get("amount", "").strip())
    except ValueError:
        amount = 0

    if not donor_name or payment_method not in PAYMENT_METHODS or amount <= 0 or not contact:
        return False, "Please complete all required fields."
    if disaster_id and disaster_repository.find_approved(disaster_id) is None:
        return False, "Please choose a valid approved disaster."

    donation_repository.create(disaster_id, donor_name, payment_method, amount, contact)
    return True, None


def list_public():
    return donation_repository.list_public()


def admin_report(filters):
    return donation_repository.admin_report(filters)


def moderate(donation_id, action):
    if action not in ("approve", "reject"):
        return None
    status = "approved" if action == "approve" else "rejected"
    return status if donation_repository.update_status(donation_id, status) else None

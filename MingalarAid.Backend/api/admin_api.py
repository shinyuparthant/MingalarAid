from flask import abort, flash, redirect, render_template, request, url_for

from api.guards import admin_required
from service import disaster_service, donation_service, volunteer_service


def register_admin_api(app):
    @app.route("/admin")
    @admin_required
    def admin_dashboard():
        filters = {
            "date": request.args.get("date", "").strip(),
            "month": request.args.get("month", "").strip(),
            "year": request.args.get("year", "").strip(),
            "disaster_id": request.args.get("disaster_id", "").strip(),
        }
        pending, all_disasters, disaster_options = disaster_service.admin_snapshot()
        donations, total_donations = donation_service.admin_report(filters)
        return render_template(
            "admin_dashboard.html",
            pending=pending,
            all_disasters=all_disasters,
            donations=donations,
            total_donations=total_donations,
            disaster_options=disaster_options,
            selected_date=filters["date"],
            selected_month=filters["month"],
            selected_year=filters["year"],
            selected_disaster=filters["disaster_id"],
            volunteers=volunteer_service.list_all(),
        )

    @app.route("/admin/disasters/<int:disaster_id>/<action>", methods=["POST"])
    @admin_required
    def moderate_disaster(disaster_id, action):
        status = disaster_service.moderate(disaster_id, action)
        if status is None:
            abort(404)
        flash(f"Report {status}.", "success")
        return redirect(url_for("admin_dashboard"))

    @app.route("/admin/donations/<int:donation_id>/<action>", methods=["POST"])
    @admin_required
    def moderate_donation(donation_id, action):
        status = donation_service.moderate(donation_id, action)
        if status is None:
            abort(404)
        flash(f"Donation {status}.", "success")
        return redirect(request.referrer or url_for("admin_dashboard"))

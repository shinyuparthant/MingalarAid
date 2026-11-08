from flask import abort, flash, redirect, render_template, request, url_for

from api.guards import user_required
from service import disaster_service, donation_service, volunteer_service


def register_public_api(app):
    @app.route("/")
    def index():
        return render_template("index.html", disasters=disaster_service.latest())

    @app.route("/disasters")
    def disasters():
        return render_template("disasters.html", disasters=disaster_service.list_public())

    @app.route("/disasters/<int:disaster_id>")
    def disaster_detail(disaster_id):
        disaster = disaster_service.get_public(disaster_id)
        if disaster is None:
            abort(404)
        return render_template("disaster_detail.html", disaster=disaster)

    @app.route("/report", methods=["GET", "POST"])
    @user_required
    def report_disaster():
        if request.method == "POST":
            success, error = disaster_service.submit_report(request.form)
            if not success:
                flash(error, "error")
                return render_template("report.html")
            flash("Your report was submitted for administrator review. Thank you.", "success")
            return redirect(url_for("report_disaster"))
        return render_template("report.html")

    @app.route("/donate", methods=["GET", "POST"])
    @user_required
    def donate():
        approved = disaster_service.approved_options()
        if request.method == "POST":
            success, error = donation_service.submit(request.form)
            if not success:
                flash(error, "error")
                return render_template("donate.html", disasters=approved)
            flash("Thank you! Your donation is waiting for administrator confirmation.", "success")
            return redirect(url_for("donate"))
        return render_template("donate.html", disasters=approved)

    @app.route("/donations")
    def public_donations():
        return render_template("donations.html", donations=donation_service.list_public())

    @app.route("/volunteer", methods=["GET", "POST"])
    @user_required
    def volunteer():
        approved = disaster_service.approved_options()
        if request.method == "POST":
            success, error = volunteer_service.submit(request.form)
            if not success:
                flash(error, "error")
                return render_template("volunteer.html", disasters=approved)
            flash("Thank you for offering to volunteer. An organizer can contact you.", "success")
            return redirect(url_for("volunteer"))
        return render_template("volunteer.html", disasters=approved)

    @app.route("/volunteers")
    def public_volunteers():
        return render_template("volunteers.html", volunteers=volunteer_service.list_public())

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("404.html"), 404

from flask import flash, redirect, render_template, request, session, url_for

from service import auth_service


def register_auth_api(app):
    def start_session(user):
        session.clear()
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["role"] = user["role"]

    @app.route("/login", methods=["GET", "POST"])
    def user_login():
        if request.method == "POST":
            user = auth_service.authenticate(
                request.form.get("username", ""), request.form.get("password", "")
            )
            if user:
                start_session(user)
                flash("You are signed in.", "success")
                next_url = request.args.get("next", "")
                if next_url.startswith("/") and not next_url.startswith("//"):
                    return redirect(next_url)
                return redirect(url_for("index"))
            flash("Incorrect username or password.", "error")
        return render_template("user_login.html")

    @app.route("/logout")
    def user_logout():
        session.clear()
        flash("You have been signed out.", "success")
        return redirect(url_for("index"))

    @app.route("/admin/login", methods=["GET", "POST"])
    def admin_login():
        if request.method == "POST":
            user = auth_service.authenticate(
                request.form.get("username", ""),
                request.form.get("password", ""),
                required_role="admin",
            )
            if user:
                start_session(user)
                flash("You are signed in.", "success")
                return redirect(url_for("admin_dashboard"))
            flash("Incorrect username or password.", "error")
        return render_template("admin_login.html")

    @app.route("/admin/logout")
    def admin_logout():
        session.clear()
        flash("You have been signed out.", "success")
        return redirect(url_for("index"))

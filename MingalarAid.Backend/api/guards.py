from functools import wraps

from flask import flash, redirect, request, session, url_for


def user_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in to continue.", "error")
            return redirect(url_for("user_login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Please sign in as an administrator first.", "error")
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)

    return wrapped

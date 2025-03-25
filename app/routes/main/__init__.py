from flask import Blueprint, render_template, session, redirect, url_for

bp = Blueprint("main", __name__)


@bp.before_request
def before_request_callback():
    if "client_id" not in session:
        return redirect(url_for("auth.index"))


@bp.route("/", methods=["GET"])
def index():
    return render_template("pages/index.jinja")

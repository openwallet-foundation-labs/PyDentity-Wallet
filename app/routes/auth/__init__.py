from flask import Blueprint, render_template, session, redirect, url_for
from config import Config

bp = Blueprint("auth", __name__)


@bp.route("/")
def index():
    session.clear()
    session["endpoint"] = Config.APP_URL
    return render_template("pages/auth.jinja", title=Config.APP_NAME)


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.index"))

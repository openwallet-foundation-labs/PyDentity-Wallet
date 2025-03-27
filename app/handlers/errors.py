from flask import Blueprint, render_template
from werkzeug.exceptions import HTTPException

bp = Blueprint("errors", __name__)


@bp.app_errorhandler(HTTPException)
def handle_http_exception(error):
    return render_template("pages/error.jinja", title="Error", error=error)

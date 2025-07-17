from flask import (
    Blueprint,
    current_app,
    request,
    jsonify,
    render_template,
    session,
    redirect,
    url_for,
)
from app.plugins import QRScanner
from app.operations import sync_session
from asyncio import run as await_

bp = Blueprint("main", __name__)


@bp.before_request
def before_request_callback():
    if not session.get("client_id"):
        return redirect(url_for("auth.index"))


@bp.route("/", methods=["GET"])
def index():
    await_(sync_session(session.get("client_id")))
    return render_template("pages/index.jinja")


@bp.route("/scanner", methods=["POST"])
def scan_qr_code():
    current_app.logger.warning("QR Scanner")
    qr_scanner = QRScanner(session["client_id"])
    await_(qr_scanner.handle_payload(request.form["payload"]))
    return jsonify({"status": "ok"})

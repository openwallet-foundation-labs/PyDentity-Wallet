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
from asyncio import run as await_
from time import sleep

bp = Blueprint("main", __name__)


@bp.before_request
def before_request_callback():
    if not session.get("wallet_id"):
        return redirect(url_for("auth.index"))


@bp.route("/", methods=["GET"])
def index():
    return render_template("pages/index.jinja")


@bp.route("/scanner", methods=["POST"])
def scan_qr_code():
    current_app.logger.warning("QR Scanner")

    current_app.logger.warning(session["wallet_id"])
    qr_scanner = QRScanner(session["client_id"], session["wallet_id"])
    await_(qr_scanner.handle_payload(request.form["payload"]))
    sleep(2)
    return jsonify({"status": "ok"})

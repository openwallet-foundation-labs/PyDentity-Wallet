from flask import (
    Blueprint,
    current_app,
    render_template,
    session,
    redirect,
    url_for,
    request,
    jsonify,
)
from app.plugins import QRScanner
from app.operations import sync_session, sync_wallet
from asyncio import run as await_

bp = Blueprint("main", __name__)


@bp.before_request
def before_request_callback():
    if not session.get("wallet_id"):
        return redirect(url_for("auth.index"))


@bp.route("/", methods=["GET"])
def index():
    current_app.logger.warning(session["wallet_id"])
    await_(sync_session(session.get("wallet_id")))
    # current_app.logger.warning(session["connections"])
    # current_app.logger.warning(session["credentials"])
    return render_template("pages/index.jinja")


@bp.route("/sync", methods=["GET"])
def sync():
    current_app.logger.warning("Wallet Sync")
    current_app.logger.warning(session["wallet_id"])
    await_(sync_wallet(session.get("wallet_id")))
    return redirect(url_for("main.index"))


@bp.route("/scanner", methods=["POST"])
def scan_qr_code():
    current_app.logger.warning("QR Scanner")

    current_app.logger.warning(session["wallet_id"])
    qr_scanner = QRScanner(session["client_id"], session["wallet_id"])
    await_(qr_scanner.handle_payload(request.form["payload"]))
    return jsonify({"status": "ok"})

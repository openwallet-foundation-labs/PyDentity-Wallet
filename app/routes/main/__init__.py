from flask import Blueprint, current_app, render_template, session, redirect, url_for, request, jsonify
from .scanner import QRScanner
from asyncio import run as await_

bp = Blueprint("main", __name__)


@bp.before_request
def before_request_callback():
    if not session.get("wallet_id"):
        return redirect(url_for("auth.index"))


@bp.route("/", methods=["GET"])
def index():
    return render_template("pages/index.jinja")


@bp.route("/scanner", methods=["POST"])
def qr_scanner():
    current_app.logger.warning("QR Scanner")
    await_(QRScanner(session["wallet_id"]).handle_payload(request.form["payload"]))
    return jsonify({"status": "ok"})

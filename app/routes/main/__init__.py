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
    qr_scanner = QRScanner(session["wallet_id"])
    result = await_(qr_scanner.handle_payload(request.form["payload"]))
    
    # Return success with message about what was processed
    return jsonify({
        "status": "success", 
        "message": "QR code processed successfully",
        "result": result
    })


@bp.route("/connection-status", methods=["GET"])
def get_connection_status():
    """Get the current connection state"""
    from app.plugins import AgentController, AskarStorage
    from asyncio import run as await_
    
    # Get the latest connection ID from session or most recent connection
    connections = session.get('connections', [])
    if not connections:
        return jsonify({"state": "no_connection", "connected": False})
    
    # Get the most recent connection
    latest_connection = connections[-1] if connections else None
    if not latest_connection:
        return jsonify({"state": "no_connection", "connected": False})
    
    connection_id = latest_connection.get('connection_id')
    
    agent = AgentController()
    askar = AskarStorage()
    
    # Get wallet and set token
    wallet = await_(askar.fetch("wallet", session.get("wallet_id")))
    agent.set_token(wallet["token"])
    
    try:
        connection_info = agent.get_connection_info(connection_id)
        state = connection_info.get('state', 'unknown')
        connected = state in ['active', 'completed', 'response']
        
        return jsonify({
            "state": state,
            "connected": connected,
            "their_label": connection_info.get('their_label', 'Unknown')
        })
    except Exception as e:
        current_app.logger.error(f"Error getting connection status: {e}")
        return jsonify({"state": "error", "connected": False, "error": str(e)})


@bp.route("/credential-offers", methods=["GET"])
def get_credential_offers():
    """Get pending credential offers for the user"""
    from app.plugins import AskarStorage
    askar = AskarStorage()
    
    offers = await_(askar.fetch("cred_ex", session.get("client_id")))
    return jsonify({"offers": offers or []})


@bp.route("/credential-offer/<exchange_id>", methods=["GET"])
def credential_offer(exchange_id):
    """View credential offer details"""
    from app.plugins import AgentController, AskarStorage
    from asyncio import run as await_
    
    agent = AgentController()
    askar = AskarStorage()
    
    # Get wallet and set token
    wallet = await_(askar.fetch("wallet", session.get("wallet_id")))
    agent.set_token(wallet["token"])
    
    try:
        # Fetch credential offer details
        offer_details = agent.get_credential_exchange(exchange_id)
        
        # Parse offer data for display
        offer = {
            "exchange_id": exchange_id,
            "credential_name": offer_details.get("credential_name", "Credential"),
            "issuer": offer_details.get("issuer", {}),
            "attributes": offer_details.get("credential_preview", {}).get("attributes", {}),
            "state": offer_details.get("state"),
        }
        
        return render_template("pages/credential-offer.jinja", offer=offer, exchange_id=exchange_id)
    except Exception as e:
        current_app.logger.error(f"Error fetching credential offer: {e}")
        return redirect(url_for("main.index"))


@bp.route("/credential-offers/<exchange_id>/accept", methods=["POST"])
def accept_credential_offer(exchange_id):
    """Accept a credential offer"""
    from app.plugins import AgentController, AskarStorage
    from asyncio import run as await_
    
    agent = AgentController()
    askar = AskarStorage()
    
    # Get wallet and set token
    wallet = await_(askar.fetch("wallet", session.get("wallet_id")))
    agent.set_token(wallet["token"])
    
    try:
        # Send credential request
        response = agent.send_credential_request(exchange_id)
        return jsonify({"status": "success", "message": "Credential request sent"})
    except Exception as e:
        current_app.logger.error(f"Error accepting credential offer: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400


@bp.route("/credential-offers/<exchange_id>/decline", methods=["POST"])
def decline_credential_offer(exchange_id):
    """Decline a credential offer"""
    from app.plugins import AgentController, AskarStorage
    from asyncio import run as await_
    
    agent = AgentController()
    askar = AskarStorage()
    
    # Get wallet and set token
    wallet = await_(askar.fetch("wallet", session.get("wallet_id")))
    agent.set_token(wallet["token"])
    
    try:
        # Send decline message
        response = agent.send_credential_decline(exchange_id)
        return jsonify({"status": "success", "message": "Credential offer declined"})
    except Exception as e:
        current_app.logger.error(f"Error declining credential offer: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400


@bp.route("/presentation-requests/<exchange_id>/respond", methods=["POST"])
def respond_to_presentation_request(exchange_id):
    """Respond to a presentation request"""
    from app.plugins import AgentController, AskarStorage
    from asyncio import run as await_
    
    agent = AgentController()
    askar = AskarStorage()
    
    # Get wallet and set token
    wallet = await_(askar.fetch("wallet", session.get("wallet_id")))
    agent.set_token(wallet["token"])
    
    try:
        # Get presentation request details
        pres_request = request.json
        # Send presentation response
        response = agent.send_presentation_response(exchange_id, pres_request)
        return jsonify({"status": "success", "message": "Presentation response sent"})
    except Exception as e:
        current_app.logger.error(f"Error responding to presentation request: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400

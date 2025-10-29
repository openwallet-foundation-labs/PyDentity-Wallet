from flask import Blueprint, abort,  render_template, url_for, current_app, session, redirect, jsonify, request
import asyncio
from asyncio import run as await_
from app.plugins import AskarStorage, AgentController, AskarStorageKeys
# from app.operations import beautify_anoncreds
from .manager import WebhookManager
from .models import Message, CredentialOffer, PresentationRequest, Notification
from config import Config

bp = Blueprint("webhooks", __name__)


@bp.before_request
def before_request_callback():
    api_key = request.headers.get('X-API-KEY')
    if not api_key:
        return {"message": "Unauthorized"}, 401
    elif api_key != Config.AGENT_ADMIN_API_KEY:
        return {"message": "Unauthorized"}, 401

@bp.route("/topic/<topic>/", methods=["POST"])
def webhook_topic(topic: str):
    wallet_id = request.headers.get('X-WALLET-ID')
    current_app.logger.info(f"Webhook received for wallet: {wallet_id}, topic: {topic}")
    
    # Fetch wallet from storage using wallet-specific askar instance
    wallet_askar = AskarStorage.for_wallet(wallet_id)
    if not (wallet := await_(wallet_askar.fetch(AskarStorageKeys.WALLETS))):
        current_app.logger.error(f"Wallet not found: {wallet_id}")
        return {"message": "Wallet not found"}, 404
    
    return await_(
        WebhookManager(wallet).handle_topic(topic, request.json)
    )
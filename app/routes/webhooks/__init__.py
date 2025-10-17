from flask import Blueprint, abort,  render_template, url_for, current_app, session, redirect, jsonify, request
import asyncio
from asyncio import run as await_
from app.plugins import AskarStorage, AgentController
# from app.operations import beautify_anoncreds
from .manager import WebhookManager
from .models import Message, CredentialOffer, PresentationRequest, Notification
from config import Config

bp = Blueprint("webhooks", __name__)

askar = AskarStorage()


@bp.before_request
def before_request_callback():
    api_key = request.headers.get('X-API-KEY')
    if not api_key:
        return {"message": "Unauthorized"}, 401
    elif api_key != Config.AGENT_ADMIN_API_KEY:
        return {"message": "Unauthorized"}, 401

@bp.route("/topic/<topic>/", methods=["POST"])
def webhook_topic(topic: str):
    return await_(
        WebhookManager(
            request.headers.get('X-WALLET-ID')
        ).handle_topic(topic, request.json)
    )
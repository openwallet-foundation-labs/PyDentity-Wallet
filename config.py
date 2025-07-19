import redis
import os
import ngrok
from pathlib import Path
from dotenv import load_dotenv
from cachelib.file import FileSystemCache
from qrcode import QRCode

load_dotenv()


class Config(object):
    ENV = os.getenv("PYDENTITY_WALLET_ENV", "development")
    DEBUG = True if ENV == "development" else False
    TESTING = True if ENV == "development" else False

    DOMAIN = os.getenv("PYDENTITY_WALLET_DOMAIN", "localhost")
    APP_URL = os.getenv("PYDENTITY_WALLET_APP_URL", "http://localhost:5000")
    APP_NAME = os.getenv("PYDENTITY_WALLET_APP_NAME", "PyDentity Wallet")
    APP_ICON = os.getenv(
        "PYDENTITY_WALLET_APP_ICON",
        "https://raw.githubusercontent.com/openwallet-foundation-labs/PyDentity-Wallet/refs/heads/main/assets/pydentity-icon.png",
    )
    APP_LOGO = os.getenv(
        "PYDENTITY_WALLET_APP_LOGO",
        "https://raw.githubusercontent.com/openwallet-foundation-labs/PyDentity-Wallet/refs/heads/main/assets/pydentity-logo.png",
    )

    PROJECT_URL = "https://github.com/openwallet-foundation-labs/PyDentity-Wallet"

    SECRET_KEY = os.getenv("PYDENTITY_WALLET_SECRET_KEY", "unsecured")

    # Create local storage if no postgres instance available
    ASKAR_DB = os.getenv("ASKAR_DB", "sqlite://app.db")

    # Create local cache if no redis instance available
    if os.getenv("REDIS_URL"):
        SESSION_TYPE = "redis"
        SESSION_REDIS = redis.from_url(os.getenv("REDIS_URL"))
        REGISTRATION_CHALLENGES = SESSION_REDIS
        AUTHENTICATION_CHALLENGES = SESSION_REDIS
    else:
        Path("session").mkdir(parents=True, exist_ok=True)
        SESSION_TYPE = "cachelib"
        SESSION_SERIALIZATION_FORMAT = "json"
        SESSION_CACHELIB = FileSystemCache(threshold=500, cache_dir="session")
        REGISTRATION_CHALLENGES = SESSION_CACHELIB
        AUTHENTICATION_CHALLENGES = SESSION_CACHELIB

    AGENT_ADMIN_API_KEY = os.getenv("AGENT_ADMIN_API_KEY")
    AGENT_ADMIN_ENDPOINT = os.getenv("AGENT_ADMIN_ENDPOINT")

    SESSION_COOKIE_NAME = "PyDentity"
    SESSION_COOKIE_SAMESITE = "Strict"
    SESSION_COOKIE_HTTPONLY = "True"

    JSONIFY_PRETTYPRINT_REGULAR = True

    NGROK_AUTHTOKEN = os.getenv("NGROK_AUTHTOKEN", None)
    if NGROK_AUTHTOKEN:
        listener = ngrok.werkzeug_develop()
        APP_URL = listener.url()
        DOMAIN = APP_URL.split("https://")[-1]
        print(APP_URL)
        qr = QRCode(box_size=10, border=4)
        qr.add_data(listener.url())
        qr.print_ascii()

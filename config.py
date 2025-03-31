import redis
import os
from pathlib import Path
from dotenv import load_dotenv
from cachelib.file import FileSystemCache

load_dotenv()


class Config(object):
    ENV = os.getenv("PYDENTITY_WALLET_ENV", "development")
    DEBUG = True if ENV == "development" else False
    TESTING = True if ENV == "development" else False

    DOMAIN = os.getenv("PYDENTITY_WALLET_DOMAIN", "localhost")
    APP_URL = os.getenv("PYDENTITY_WALLET_APP_URL", f"https://{DOMAIN}")
    APP_NAME = "PyDentity Wallet"

    PROJECT_URL = "https://github.com/openwallet-foundation-labs/PyDentity-Wallet"

    SECRET_KEY = os.getenv("PYDENTITY_WALLET_SECRET_KEY", "unsecured")

    # Create local storage if no postgres instance available
    ASKAR_DB = os.getenv("ASKAR_DB", "sqlite://app.db")

    SESSION_TYPE = "redis"
    SESSION_REDIS = redis.from_url(os.getenv("REDIS_URL"))
    
    AGENT_ADMIN_API_KEY = os.getenv('AGENT_ADMIN_API_KEY')
    AGENT_ADMIN_ENDPOINT = os.getenv('AGENT_ADMIN_ENDPOINT')

    SESSION_COOKIE_NAME = "PyDentity"
    SESSION_COOKIE_SAMESITE = "Strict"
    SESSION_COOKIE_HTTPONLY = "True"

    JSONIFY_PRETTYPRINT_REGULAR = True

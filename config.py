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

    DOMAIN = os.getenv("DOMAIN", "localhost")

    APP_NAME = "PyDentity Wallet"
    APP_URL = os.getenv("DOMAIN", f"https://{DOMAIN}")

    PROJECT_URL = "https://github.com/openwallet-foundation-labs/PyDentity-Wallet"

    SECRET_KEY = os.getenv("SECRET_KEY", "unsecured")

    # Create local storage if no postgres instance available
    ASKAR_DB = os.getenv("ASKAR_DB", "sqlite://app.db")

    # Create local cache if no redis instance available
    if os.getenv("REDIS_URL"):
        SESSION_TYPE = "redis"
        SESSION_REDIS = redis.from_url(os.getenv("REDIS_URL"))
    else:
        Path("session").mkdir(parents=True, exist_ok=True)
        SESSION_TYPE = "cachelib"
        SESSION_SERIALIZATION_FORMAT = "json"
        SESSION_CACHELIB = FileSystemCache(threshold=500, cache_dir="session")

    SESSION_COOKIE_NAME = "PyDentity"
    SESSION_COOKIE_SAMESITE = "Strict"
    SESSION_COOKIE_HTTPONLY = "True"

    JSONIFY_PRETTYPRINT_REGULAR = True

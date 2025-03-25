from aries_askar import Store
import hashlib
import logging
from config import Config

logger = logging.getLogger(__name__)


class AskarStorage:
    def __init__(self):
        self.db = Config.ASKAR_DB
        self.key = Store.generate_raw_key(
            hashlib.md5(Config.SECRET_KEY.encode()).hexdigest()
        )

    async def provision(self, recreate=False):
        logger.warning(self.db)
        await Store.provision(self.db, "raw", self.key, recreate=recreate)

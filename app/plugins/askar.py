from aries_askar import Store, AskarError
import hashlib
import logging
import json
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

    async def open(self):
        return await Store.open(self.db, "raw", self.key)

    async def fetch(self, category, data_key):
        store = await self.open()
        try:
            async with store.session() as session:
                entry = await session.fetch(category, data_key)
            return json.loads(entry.value)
        except (AskarError, ValueError, KeyError):
            return None

    async def fetch_name_by_tag(self, category, tags):
        store = await self.open()
        try:
            async with store.session() as session:
                entries = await session.fetch_all(category, tags)
            return entries.handle.get_name(0)
        except (AskarError, IndexError):
            return None

    async def fetch_entry_by_tag(self, category, tags):
        store = await self.open()
        try:
            async with store.session() as session:
                entries = await session.fetch_all(category, tags)
                entries = entries.handle.get_value(0)
            return json.loads(entries)
        except (AskarError, ValueError, IndexError):
            return None

    async def store(self, category, data_key, data, tags=None):
        store = await self.open()
        try:
            # current_app.logger.warning(data)
            async with store.session() as session:
                await session.insert(
                    category,
                    data_key,
                    json.dumps(data),
                    tags,
                )
        except (AskarError, ValueError):
            return False

    async def append(self, category, data_key, data, tags=None):
        store = await self.open()
        try:
            async with store.session() as session:
                entries = await session.fetch(category, data_key)
                entries = json.loads(entries.value)
                entries.append(data)
                await session.replace(
                    category,
                    data_key,
                    json.dumps(entries),
                    tags,
                )
        except (AskarError, ValueError):
            return False

    async def update(self, category, data_key, data, tags=None):
        store = await self.open()
        try:
            async with store.session() as session:
                await session.replace(
                    category,
                    data_key,
                    json.dumps(data),
                    tags,
                )
        except (AskarError, ValueError):
            return False

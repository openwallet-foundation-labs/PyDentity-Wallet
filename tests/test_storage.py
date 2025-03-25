import pytest
from app.plugins import AskarStorage

askar = AskarStorage()

@pytest.mark.asyncio
async def test_storage():
    await askar.provision(recreate=True)

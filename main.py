from app import create_app
from app.plugins import AskarStorage
from asyncio import run as _await

app = create_app()

if __name__ == "__main__":
    _await(AskarStorage().provision(recreate=False))
    app.run(host="0.0.0.0", port="5000")

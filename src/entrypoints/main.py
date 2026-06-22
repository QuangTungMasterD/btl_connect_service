# src/entrypoints/main.py

import asyncio
import uvicorn

from src.api.app import app
from src.entrypoints.run_consumer import main as consumer_main

from src.infrastructure.database.models import Base
from src.infrastructure.database.session import engine

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def start_api():
    config = uvicorn.Config(
        "src.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    await init_db()
    await asyncio.gather(
        start_api(),
        consumer_main()
    )

if __name__ == "__main__":
    asyncio.run(main())
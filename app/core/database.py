from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import get_settings
from app.core.logging import logger


settings = get_settings()

_client: AsyncIOMotorClient | None = None



async def connect_db() -> None:
    global _client
    logger.info("Connecting to MongoDB...")
    _client = AsyncIOMotorClient(settings.MONGO_URI)
    # Verify real connection
    await _client.admin.command("ping")
    logger.info(f"MongoDB connected successfully. DB: {settings.DB_NAME}")


async def disconnect_db() -> None:
    global _client
    if _client is not None:
        _client.close()
        logger.info("MongoDB connection closed.")


def get_database() -> AsyncIOMotorDatabase:
    """
        Dependency to inject the database into services.
        Use: db: AsyncIOMotorDatabase = Depends(get_database)
    """
    if _client is None:
        raise RuntimeError("MongoDB not connected. Verify the startup.")
    return _client[settings.DB_NAME]


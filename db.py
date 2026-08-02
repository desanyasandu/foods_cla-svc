"""Async MongoDB database connection module using Motor."""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from motor.core import AgnosticCollection
import os
import logging

logger = logging.getLogger(__name__)

client: AsyncIOMotorClient | None = None
db: AsyncIOMotorDatabase | None = None


def init_client(mongo_url: str | None = None) -> AsyncIOMotorClient:
    """Initialize the MongoDB client."""
    global client, db
    if mongo_url is None:
        mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongo_url)
    db = client["food_ai"]
    logger.info("MongoDB database initialized")
    return client


def get_database() -> AsyncIOMotorDatabase:
    """Get the database instance."""
    if db is None:
        raise RuntimeError("Database not initialized. Call init_client() first.")
    return db


async def get_foods_collection() -> AgnosticCollection:
    """Get the foods collection."""
    return get_database()["foods"]


async def get_nutrition_collection() -> AgnosticCollection:
    """Get the nutrition collection."""
    return get_database()["nutrition"]


async def get_meals_collection() -> AgnosticCollection:
    """Get the meals collection."""
    return get_database()["meals"]


async def get_detections_collection() -> AgnosticCollection:
    """Get the detections collection."""
    return get_database()["detections"]


async def get_users_collection() -> AgnosticCollection:
    """Get the users collection."""
    return get_database()["users"]


def close_client() -> None:
    """Close the MongoDB client connection."""
    global client, db
    if client:
        client.close()
        logger.info("MongoDB client connection closed")
        client = None
        db = None
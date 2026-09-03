"""
MongoDB connection setup and database management
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from pymongo import ASCENDING
from pymongo.errors import ConnectionFailure
from datetime import datetime, timedelta
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Global MongoDB client and database instances
client: AsyncIOMotorClient = None
database = None
gridfs_bucket: AsyncIOMotorGridFSBucket = None


async def connect_to_mongodb():
    """
    Establish connection to MongoDB Atlas
    Initialize GridFS for file storage
    Create necessary indexes
    """
    global client, database, gridfs_bucket
    
    try:
        # Create MongoDB client
        client = AsyncIOMotorClient(settings.MONGO_URI)
        
        # Test connection
        await client.admin.command('ping')
        logger.info("Successfully connected to MongoDB Atlas")
        
        # Initialize database
        database = client[settings.MONGO_DATABASE]
        
        # Initialize GridFS for file storage
        gridfs_bucket = AsyncIOMotorGridFSBucket(database)
        
        # Create indexes
        await create_indexes()
        
        logger.info(f"Database '{settings.MONGO_DATABASE}' initialized with GridFS")
        
    except ConnectionFailure as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


async def create_indexes():
    """
    Create necessary indexes for optimal query performance
    """
    try:
        # Index on conveyancers province field
        await database.conveyancers.create_index([("province", ASCENDING)])
        logger.info("Created index on conveyancers.province")
        
        # Index on conveyancers company_name for alphabetical sorting
        await database.conveyancers.create_index([("company_name", ASCENDING)])
        logger.info("Created index on conveyancers.company_name")
        
        # TTL index on sessions collection (48-hour expiration)
        expiry_time = timedelta(hours=settings.SESSION_EXPIRY_HOURS)
        await database.sessions.create_index(
            [("updated_at", ASCENDING)],
            expireAfterSeconds=int(expiry_time.total_seconds())
        )
        logger.info(f"Created TTL index on sessions.updated_at ({settings.SESSION_EXPIRY_HOURS} hours)")
        
        # Index on applications owner_phone for user queries
        await database.applications.create_index([("owner_phone", ASCENDING)])
        logger.info("Created index on applications.owner_phone")
        
        # Index on applications created_at for sorting
        await database.applications.create_index([("created_at", ASCENDING)])
        logger.info("Created index on applications.created_at")
        
        # Index on applications verification status
        await database.applications.create_index([("verification.status", ASCENDING)])
        logger.info("Created index on applications.verification.status")
        
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")
        raise


async def close_mongodb_connection():
    """
    Close MongoDB connection
    """
    global client, database, gridfs_bucket
    
    if client:
        client.close()
        logger.info("MongoDB connection closed")
        client = None
        database = None
        gridfs_bucket = None


def get_database():
    """
    Get database instance
    """
    if database is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongodb() first.")
    return database


def get_gridfs_bucket():
    """
    Get GridFS bucket instance
    """
    if gridfs_bucket is None:
        raise RuntimeError("GridFS not initialized. Call connect_to_mongodb() first.")
    return gridfs_bucket


async def health_check():
    """
    Check MongoDB connection health
    """
    try:
        if client is None:
            return False
        
        await client.admin.command('ping')
        return True
    except Exception as e:
        logger.error(f"MongoDB health check failed: {e}")
        return False
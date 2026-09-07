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
    Includes indexes for new SLA, ledger, and audit collections
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
        
        # NEW: Index on applications case_status for SLA queries
        await database.applications.create_index([("case_status", ASCENDING)])
        logger.info("Created index on applications.case_status")
        
        # NEW: Index on applications conflict_check_status
        await database.applications.create_index([("conflict_check_status", ASCENDING)])
        logger.info("Created index on applications.conflict_check_status")
        
        # NEW: Index on sla_timers deadline_at for timeout checking
        await database.sla_timers.create_index([("deadline_at", ASCENDING)])
        logger.info("Created index on sla_timers.deadline_at")
        
        # NEW: Index on sla_timers state for active timer queries
        await database.sla_timers.create_index([("state", ASCENDING)])
        logger.info("Created index on sla_timers.state")
        
        # NEW: Index on sla_timers case_id
        await database.sla_timers.create_index([("case_id", ASCENDING)])
        logger.info("Created index on sla_timers.case_id")
        
        # NEW: Index on platform_ledgers case_id
        await database.platform_ledgers.create_index([("case_id", ASCENDING)])
        logger.info("Created index on platform_ledgers.case_id")
        
        # NEW: Index on platform_ledgers idempotency_key for idempotency
        await database.platform_ledgers.create_index([("idempotency_key", ASCENDING)], unique=True)
        logger.info("Created unique index on platform_ledgers.idempotency_key")
        
        # NEW: Index on platform_ledgers allocation_type and state
        await database.platform_ledgers.create_index([("allocation_type", ASCENDING), ("state", ASCENDING)])
        logger.info("Created index on platform_ledgers.allocation_type, state")
        
        # NEW: Index on escrow_vaults case_id
        await database.escrow_vaults.create_index([("case_id", ASCENDING)], unique=True)
        logger.info("Created unique index on escrow_vaults.case_id")
        
        # NEW: Index on escrow_vaults firm_id
        await database.escrow_vaults.create_index([("firm_id", ASCENDING)])
        logger.info("Created index on escrow_vaults.firm_id")
        
        # NEW: Index on dossier_access_events case_id and occurred_at
        await database.dossier_access_events.create_index([("case_id", ASCENDING), ("occurred_at", -1)])
        logger.info("Created index on dossier_access_events.case_id, occurred_at")
        
        # NEW: Index on dossier_access_events actor_id
        await database.dossier_access_events.create_index([("actor_id", ASCENDING)])
        logger.info("Created index on dossier_access_events.actor_id")
        
        # NEW: Index on law_firms status
        await database.law_firms.create_index([("status", ASCENDING)])
        logger.info("Created index on law_firms.status")
        
        # NEW: Index on firm_practitioners firm_id
        await database.firm_practitioners.create_index([("firm_id", ASCENDING)])
        logger.info("Created index on firm_practitioners.firm_id")
        
        logger.info("All database indexes created successfully")
        
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
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get MongoDB URI and Database Name from .env
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "knowledge_manager")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure MongoDB credentials are present
if not MONGODB_URI:
    logger.error("❌ MONGODB_URI is missing from .env! Please check your configuration.")
    exit(1)

try:
    # Connect to MongoDB with the correct URI
    logger.info(f"🔗 Connecting to MongoDB: {MONGODB_URI}")
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=10000)  # 10-second timeout

    # Test connection by pinging the database
    client.admin.command("ping")
    logger.info("✅ Successfully connected to MongoDB!")

    # Use the correct database
    db = client[MONGODB_DB_NAME]
    logger.info(f"✅ Connected to database: {MONGODB_DB_NAME}")

    # Define collections to be created
    collections = {
        "conversations": [
            ("user_id", 1),
            ("tags", 1),
            ("categories", 1),
            ("created_at", -1),
            ("title", "text"),  # Text index for search
            ("content", "text"),
        ],
        "users": [("email", 1)],  # Unique email index
        "embeddings": [("conversation_id", 1)],
    }

    # Create collections and indexes
    for collection_name, indexes in collections.items():
        collection = db[collection_name]

        # Create collection if it doesn't exist
        if collection_name not in db.list_collection_names():
            db.create_collection(collection_name)
            logger.info(f"📂 Created collection: {collection_name}")
        else:
            logger.info(f"✅ Collection already exists: {collection_name}")

        # Create indexes
        for index in indexes:
            if isinstance(index, tuple):
                collection.create_index([index])
            else:
                collection.create_index(index)
        logger.info(f"⚡ Indexes created for `{collection_name}`")

    logger.info("🚀 MongoDB setup complete!")

except ConnectionFailure:
    logger.error("❌ MongoDB Connection Failed! Unable to reach the database server.")
except OperationFailure as e:
    logger.error("❌ MongoDB Authentication Failed! Please check your username and password.")
    logger.error(str(e))
except Exception as e:
    logger.error(f"❌ MongoDB setup failed: {e}")

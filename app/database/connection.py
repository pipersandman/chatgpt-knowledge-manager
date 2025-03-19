import os
import logging
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

# Load environment variables
load_dotenv()

# Get MongoDB URI from .env
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "knowledge_manager")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure MongoDB credentials exist
if not MONGODB_URI:
    logger.error("❌ MONGODB_URI is missing from .env! Please check your configuration.")
    raise ValueError("MONGODB_URI is missing from .env!")

class Database:
    """Singleton class for managing MongoDB connection"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance.client = None
            cls._instance.db = None
        return cls._instance

    def connect(self):
        """Establish connection to MongoDB"""
        if not self.client:
            try:
                logger.info(f"🔗 Connecting to MongoDB: {MONGODB_URI}")
                self.client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=10000)
                self.client.admin.command("ping")  # Test connection
                self.db = self.client[MONGODB_DB_NAME]
                logger.info(f"✅ Connected to database: {MONGODB_DB_NAME}")
            except ConnectionFailure:
                logger.error("❌ MongoDB Connection Failed! Unable to reach the database server.")
                raise
            except OperationFailure as e:
                logger.error("❌ MongoDB Authentication Failed! Please check your username and password.")
                logger.error(str(e))
                raise
            except Exception as e:
                logger.error(f"❌ MongoDB setup failed: {e}")
                raise
        return self.db

# Global instance for easy import
db = Database().connect()

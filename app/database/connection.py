from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import logging
from app.config.config import MONGODB_URI, MONGODB_DB_NAME

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance.client = None
            cls._instance.db = None
        return cls._instance
    
    def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(MONGODB_URI)
            # Verify connection is successful
            self.client.admin.command('ping')
            self.db = self.client[MONGODB_DB_NAME]
            logger.info(f"Connected to MongoDB: {MONGODB_DB_NAME}")
            
            # Create indexes for better performance
            self._create_indexes()
            
            return self.db
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def _create_indexes(self):
        """Create database indexes for better query performance"""
        try:
            # Index for conversations collection
            self.db.conversations.create_index([("user_id", 1)])
            self.db.conversations.create_index([("tags", 1)])
            self.db.conversations.create_index([("categories", 1)])
            self.db.conversations.create_index([("created_at", -1)])
            
            # Index for conversations to support text search
            self.db.conversations.create_index([("title", "text"), ("content", "text")])
            
            # Index for embeddings collection
            self.db.embeddings.create_index([("conversation_id", 1)])
            
            # Index for users collection
            self.db.users.create_index([("email", 1)], unique=True)
            
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating database indexes: {e}")
    
    def close(self):
        """Close the MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

# Singleton instance
db = Database()
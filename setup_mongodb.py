from pymongo import MongoClient
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Connect to MongoDB
    client = MongoClient('mongodb://localhost:27017/')
    
    # Force a connection by executing a command
    client.admin.command('ping')
    logger.info("Successfully connected to MongoDB")
    
    # Create database (in MongoDB, it's created when you use it)
    db = client["knowledge_manager"]
    logger.info("Created/accessed database: knowledge_manager")
    
    # Create collections
    db.create_collection("conversations")
    logger.info("Created collection: conversations")
    
    db.create_collection("users")
    logger.info("Created collection: users")
    
    db.create_collection("embeddings")
    logger.info("Created collection: embeddings")
    
    logger.info("MongoDB setup complete!")
    
except Exception as e:
    logger.error(f"MongoDB setup failed: {e}")
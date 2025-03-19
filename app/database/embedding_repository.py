import logging
from typing import List, Optional, Dict, Any
from bson import ObjectId
from pymongo.errors import PyMongoError

from app.database.connection import db
from app.models.embedding import ConversationEmbedding

logger = logging.getLogger(__name__)

class EmbeddingRepository:
    """Data access layer for conversation embeddings"""
    
    def __init__(self):
        self.db = db_instance.connect()
        self.collection = self.db.embeddings
    
    def create(self, embedding: ConversationEmbedding) -> str:
        """Store a new embedding"""
        try:
            embedding_dict = embedding.to_dict()
            result = self.collection.insert_one(embedding_dict)
            logger.info(f"Created embedding with ID: {result.inserted_id}")
            return str(result.inserted_id)
        except PyMongoError as e:
            logger.error(f"Error creating embedding: {e}")
            raise
    
    def batch_create(self, embeddings: List[ConversationEmbedding]) -> int:
        """Store multiple embeddings in one operation"""
        try:
            if not embeddings:
                return 0
                
            embedding_dicts = [emb.to_dict() for emb in embeddings]
            result = self.collection.insert_many(embedding_dicts)
            logger.info(f"Created {len(result.inserted_ids)} embeddings")
            return len(result.inserted_ids)
        except PyMongoError as e:
            logger.error(f"Error creating batch embeddings: {e}")
            raise
    
    def get_by_conversation_id(self, conversation_id: str) -> List[ConversationEmbedding]:
        """Retrieve all embeddings for a specific conversation"""
        try:
            embeddings = list(self.collection.find(
                {"conversation_id": conversation_id}
            ).sort("chunk_index", 1))
            
            return [ConversationEmbedding.from_dict(emb) for emb in embeddings]
        except PyMongoError as e:
            logger.error(f"Error retrieving embeddings for conversation {conversation_id}: {e}")
            raise
    
    def delete_by_conversation_id(self, conversation_id: str) -> int:
        """Delete all embeddings for a specific conversation"""
        try:
            result = self.collection.delete_many({"conversation_id": conversation_id})
            logger.info(f"Deleted {result.deleted_count} embeddings for conversation {conversation_id}")
            return result.deleted_count
        except PyMongoError as e:
            logger.error(f"Error deleting embeddings for conversation {conversation_id}: {e}")
            raise
    
    def get_all_embeddings(self, limit: int = 1000) -> List[ConversationEmbedding]:
        """Retrieve all embeddings (with limit)"""
        try:
            embeddings = list(self.collection.find().limit(limit))
            return [ConversationEmbedding.from_dict(emb) for emb in embeddings]
        except PyMongoError as e:
            logger.error(f"Error retrieving all embeddings: {e}")
            raise
    
    def get_embedding_count(self) -> int:
        """Get the total count of embeddings"""
        try:
            return self.collection.count_documents({})
        except PyMongoError as e:
            logger.error(f"Error counting embeddings: {e}")
            raise
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId
from pymongo.errors import PyMongoError

from app.database.connection import db
from app.models.conversation import Conversation, Message

logger = logging.getLogger(__name__)

class ConversationRepository:
    """Data access layer for conversations"""
    
    def __init__(self):
        self.db = db.connect()
        self.collection = self.db.conversations
    
    def create(self, conversation: Conversation) -> str:
        """Create a new conversation record"""
        try:
            conversation_dict = conversation.to_dict()
            result = self.collection.insert_one(conversation_dict)
            logger.info(f"Created conversation with ID: {result.inserted_id}")
            return str(result.inserted_id)
        except PyMongoError as e:
            logger.error(f"Error creating conversation: {e}")
            raise
    
    def get_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """Retrieve a conversation by ID"""
        try:
            conversation_dict = self.collection.find_one({"_id": ObjectId(conversation_id)})
            if conversation_dict:
                return Conversation.from_dict(conversation_dict)
            return None
        except PyMongoError as e:
            logger.error(f"Error retrieving conversation {conversation_id}: {e}")
            raise
    
    def get_by_user(self, user_id: str, limit: int = 50, skip: int = 0) -> List[Conversation]:
        """Retrieve all conversations for a specific user"""
        try:
            conversations = list(self.collection.find(
                {"user_id": user_id}
            ).sort("updated_at", -1).skip(skip).limit(limit))
            
            return [Conversation.from_dict(conv) for conv in conversations]
        except PyMongoError as e:
            logger.error(f"Error retrieving conversations for user {user_id}: {e}")
            raise
    
    def update(self, conversation_id: str, update_data: Dict[str, Any]) -> bool:
        """Update an existing conversation"""
        try:
            # Add updated timestamp
            update_data["updated_at"] = datetime.utcnow()
            
            result = self.collection.update_one(
                {"_id": ObjectId(conversation_id)},
                {"$set": update_data}
            )
            
            logger.info(f"Updated conversation {conversation_id}: {result.modified_count} document(s) modified")
            return result.modified_count > 0
        except PyMongoError as e:
            logger.error(f"Error updating conversation {conversation_id}: {e}")
            raise
    
    def delete(self, conversation_id: str) -> bool:
        """Delete a conversation"""
        try:
            result = self.collection.delete_one({"_id": ObjectId(conversation_id)})
            logger.info(f"Deleted conversation {conversation_id}: {result.deleted_count} document(s) deleted")
            return result.deleted_count > 0
        except PyMongoError as e:
            logger.error(f"Error deleting conversation {conversation_id}: {e}")
            raise
    
    def add_message(self, conversation_id: str, message: Message) -> bool:
        """Add a new message to an existing conversation"""
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(conversation_id)},
                {
                    "$push": {"messages": message.dict()},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            logger.info(f"Added message to conversation {conversation_id}")
            return result.modified_count > 0
        except PyMongoError as e:
            logger.error(f"Error adding message to conversation {conversation_id}: {e}")
            raise
    
    def update_categories(self, conversation_id: str, categories: List[str]) -> bool:
        """Update the categories of a conversation"""
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(conversation_id)},
                {
                    "$set": {
                        "categories": categories,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            logger.info(f"Updated categories for conversation {conversation_id}")
            return result.modified_count > 0
        except PyMongoError as e:
            logger.error(f"Error updating categories for conversation {conversation_id}: {e}")
            raise
    
    def update_tags(self, conversation_id: str, tags: List[str]) -> bool:
        """Update the tags of a conversation"""
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(conversation_id)},
                {
                    "$set": {
                        "tags": tags,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            logger.info(f"Updated tags for conversation {conversation_id}")
            return result.modified_count > 0
        except PyMongoError as e:
            logger.error(f"Error updating tags for conversation {conversation_id}: {e}")
            raise
    
    def search(self, user_id: str, query: str, limit: int = 20) -> List[Conversation]:
        """Search conversations by text content"""
        try:
            # MongoDB text search
            conversations = list(self.collection.find(
                {
                    "user_id": user_id,
                    "$text": {"$search": query}
                },
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(limit))
            
            return [Conversation.from_dict(conv) for conv in conversations]
        except PyMongoError as e:
            logger.error(f"Error searching conversations for user {user_id}: {e}")
            raise
    
    def filter_by_category(self, user_id: str, category: str, limit: int = 50) -> List[Conversation]:
        """Filter conversations by category"""
        try:
            conversations = list(self.collection.find(
                {
                    "user_id": user_id,
                    "categories": category
                }
            ).sort("updated_at", -1).limit(limit))
            
            return [Conversation.from_dict(conv) for conv in conversations]
        except PyMongoError as e:
            logger.error(f"Error filtering conversations by category for user {user_id}: {e}")
            raise
    
    def filter_by_tag(self, user_id: str, tag: str, limit: int = 50) -> List[Conversation]:
        """Filter conversations by tag"""
        try:
            conversations = list(self.collection.find(
                {
                    "user_id": user_id,
                    "tags": tag
                }
            ).sort("updated_at", -1).limit(limit))
            
            return [Conversation.from_dict(conv) for conv in conversations]
        except PyMongoError as e:
            logger.error(f"Error filtering conversations by tag for user {user_id}: {e}")
            raise
    
    def get_all_categories(self, user_id: str) -> List[str]:
        """Get all unique categories used by a user"""
        try:
            categories = self.collection.distinct("categories", {"user_id": user_id})
            return categories
        except PyMongoError as e:
            logger.error(f"Error retrieving categories for user {user_id}: {e}")
            raise
    
    def get_all_tags(self, user_id: str) -> List[str]:
        """Get all unique tags used by a user"""
        try:
            tags = self.collection.distinct("tags", {"user_id": user_id})
            return tags
        except PyMongoError as e:
            logger.error(f"Error retrieving tags for user {user_id}: {e}")
            raise
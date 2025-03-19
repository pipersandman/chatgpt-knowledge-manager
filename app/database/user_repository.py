import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId
from pymongo.errors import PyMongoError, DuplicateKeyError

from app.database.connection import db
from app.models.user import User

logger = logging.getLogger(__name__)

class UserRepository:
    """Data access layer for user management"""
    
    def __init__(self):
        self.db = db_instance.connect()
        self.collection = self.db.users
    
    def create(self, user: User) -> Optional[str]:
        """Create a new user"""
        try:
            user_dict = user.to_dict()
            result = self.collection.insert_one(user_dict)
            logger.info(f"Created user with ID: {result.inserted_id}")
            return str(result.inserted_id)
        except DuplicateKeyError:
            logger.error(f"User with email {user.email} already exists")
            return None
        except PyMongoError as e:
            logger.error(f"Error creating user: {e}")
            raise
    
    def get_by_id(self, user_id: str) -> Optional[User]:
        """Retrieve a user by ID"""
        try:
            user_dict = self.collection.find_one({"_id": ObjectId(user_id)})
            if user_dict:
                return User.from_dict(user_dict)
            return None
        except PyMongoError as e:
            logger.error(f"Error retrieving user {user_id}: {e}")
            raise
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Retrieve a user by email"""
        try:
            user_dict = self.collection.find_one({"email": email})
            if user_dict:
                return User.from_dict(user_dict)
            return None
        except PyMongoError as e:
            logger.error(f"Error retrieving user by email {email}: {e}")
            raise
    
    def update(self, user_id: str, update_data: Dict[str, Any]) -> bool:
        """Update user data"""
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            logger.info(f"Updated user {user_id}: {result.modified_count} document(s) modified")
            return result.modified_count > 0
        except PyMongoError as e:
            logger.error(f"Error updating user {user_id}: {e}")
            raise
    
    def update_last_login(self, user_id: str) -> bool:
        """Update user's last login timestamp"""
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"last_login": datetime.utcnow()}}
            )
            logger.info(f"Updated last login for user {user_id}")
            return result.modified_count > 0
        except PyMongoError as e:
            logger.error(f"Error updating last login for user {user_id}: {e}")
            raise
    
    def update_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Update user preferences"""
        try:
            # Create update dict with only the fields that are present
            update_dict = {}
            if "custom_categories" in preferences:
                update_dict["custom_categories"] = preferences["custom_categories"]
            if "favorite_tags" in preferences:
                update_dict["favorite_tags"] = preferences["favorite_tags"]
            if "ui_preferences" in preferences:
                update_dict["ui_preferences"] = preferences["ui_preferences"]
            
            if not update_dict:
                logger.warning(f"No valid preference fields provided for user {user_id}")
                return False
            
            result = self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_dict}
            )
            logger.info(f"Updated preferences for user {user_id}")
            return result.modified_count > 0
        except PyMongoError as e:
            logger.error(f"Error updating preferences for user {user_id}: {e}")
            raise
    
    def delete(self, user_id: str) -> bool:
        """Delete a user"""
        try:
            result = self.collection.delete_one({"_id": ObjectId(user_id)})
            logger.info(f"Deleted user {user_id}: {result.deleted_count} document(s) deleted")
            return result.deleted_count > 0
        except PyMongoError as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            raise
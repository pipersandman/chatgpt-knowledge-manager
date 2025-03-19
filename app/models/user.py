from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, EmailStr

class User(BaseModel):
    """User model for authentication and preferences"""
    id: Optional[str] = None
    email: EmailStr
    hashed_password: str
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    
    # User preferences
    custom_categories: List[str] = []
    favorite_tags: List[str] = []
    ui_preferences: Dict[str, Any] = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user model to dictionary for database storage"""
        return {
            "email": self.email,
            "hashed_password": self.hashed_password,
            "name": self.name,
            "created_at": self.created_at,
            "last_login": self.last_login,
            "custom_categories": self.custom_categories,
            "favorite_tags": self.favorite_tags,
            "ui_preferences": self.ui_preferences
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create a User instance from a dictionary"""
        return cls(
            id=str(data.get("_id")) if "_id" in data else None,
            email=data.get("email"),
            hashed_password=data.get("hashed_password"),
            name=data.get("name"),
            created_at=data.get("created_at", datetime.utcnow()),
            last_login=data.get("last_login"),
            custom_categories=data.get("custom_categories", []),
            favorite_tags=data.get("favorite_tags", []),
            ui_preferences=data.get("ui_preferences", {})
        )


class UserCreate(BaseModel):
    """Model for user registration data"""
    email: EmailStr
    password: str
    name: str


class UserLogin(BaseModel):
    """Model for user login data"""
    email: EmailStr
    password: str


class UserPreferences(BaseModel):
    """Model for updating user preferences"""
    custom_categories: Optional[List[str]] = None
    favorite_tags: Optional[List[str]] = None
    ui_preferences: Optional[Dict[str, Any]] = None
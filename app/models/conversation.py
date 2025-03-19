from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class Message(BaseModel):
    """Individual message in a conversation"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class Conversation(BaseModel):
    """Model for storing complete conversations"""
    id: Optional[str] = None
    user_id: str
    title: str
    messages: List[Message]
    tags: List[str] = []
    categories: List[str] = []
    summary: Optional[str] = None
    key_topics: List[str] = []
    extracted_entities: List[str] = []
    important_moments: List[Dict[str, Any]] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary for database storage"""
        return {
            "user_id": self.user_id,
            "title": self.title,
            "messages": [message.dict() for message in self.messages],
            "tags": self.tags,
            "categories": self.categories,
            "summary": self.summary,
            "key_topics": self.key_topics,
            "extracted_entities": self.extracted_entities,
            "important_moments": self.important_moments,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Conversation':
        """Create a Conversation instance from a dictionary"""
        # Convert message dictionaries to Message objects
        messages = [Message(**msg) for msg in data.get("messages", [])]
        
        # Create the Conversation object with the converted messages
        return cls(
            id=str(data.get("_id")) if "_id" in data else None,
            user_id=data.get("user_id"),
            title=data.get("title"),
            messages=messages,
            tags=data.get("tags", []),
            categories=data.get("categories", []),
            summary=data.get("summary"),
            key_topics=data.get("key_topics", []),
            extracted_entities=data.get("extracted_entities", []),
            important_moments=data.get("important_moments", []),
            created_at=data.get("created_at", datetime.utcnow()),
            updated_at=data.get("updated_at", datetime.utcnow())
        )
    
    def full_text(self) -> str:
        """Get the full text of the conversation for analysis"""
        return " ".join([f"{msg.role}: {msg.content}" for msg in self.messages])
    
    def user_messages(self) -> List[Message]:
        """Get all user messages"""
        return [msg for msg in self.messages if msg.role == "user"]
    
    def assistant_messages(self) -> List[Message]:
        """Get all assistant messages"""
        return [msg for msg in self.messages if msg.role == "assistant"]
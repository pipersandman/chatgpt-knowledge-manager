from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ConversationEmbedding(BaseModel):
    """Model for storing embeddings of conversations"""
    id: Optional[str] = None
    conversation_id: str
    conversation_title: str
    text_chunk: str  # The segment of text that was embedded
    embedding: List[float]  # Vector representation
    chunk_index: int  # Position of this chunk in the conversation
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            "conversation_id": self.conversation_id,
            "conversation_title": self.conversation_title,
            "text_chunk": self.text_chunk,
            "embedding": self.embedding,
            "chunk_index": self.chunk_index,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationEmbedding':
        """Create a ConversationEmbedding instance from a dictionary"""
        return cls(
            id=str(data.get("_id")) if "_id" in data else None,
            conversation_id=data.get("conversation_id"),
            conversation_title=data.get("conversation_title"),
            text_chunk=data.get("text_chunk"),
            embedding=data.get("embedding"),
            chunk_index=data.get("chunk_index"),
            created_at=data.get("created_at", datetime.utcnow())
        )
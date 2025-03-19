import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from app.models.conversation import Conversation
from app.models.embedding import ConversationEmbedding
from app.backend.openai_service import OpenAIService
from app.database.conversation_repository import ConversationRepository
from app.database.embedding_repository import EmbeddingRepository

# Configure logging
logger = logging.getLogger(__name__)

class AnalysisService:
    """Service for analyzing and processing conversations"""
    
    def __init__(self):
        self.openai_service = OpenAIService()
        self.conversation_repo = ConversationRepository()
        self.embedding_repo = EmbeddingRepository()
    
    def process_new_conversation(self, conversation: Conversation) -> Conversation:
        """Process a new conversation: analyze, categorize, and generate embeddings"""
        try:
            # Step 1: Analyze conversation to extract topics, summary, etc.
            analysis_results = self.openai_service.analyze_conversation(conversation)
            
            # Step 2: Update conversation with analysis results
            update_data = {
                "summary": analysis_results["summary"],
                "key_topics": analysis_results["key_topics"],
                "extracted_entities": analysis_results["extracted_entities"],
                "important_moments": analysis_results["important_moments"]
            }
            
            # Step 3: Suggest tags based on key topics
            if not conversation.tags and analysis_results["key_topics"]:
                update_data["tags"] = analysis_results["key_topics"][:5]  # Use top 5 topics as tags
            
            # Step 4: Suggest categories
            if not conversation.categories:
                existing_categories = self.conversation_repo.get_all_categories(conversation.user_id)
                suggested_categories = self.openai_service.suggest_categories(conversation, existing_categories)
                update_data["categories"] = suggested_categories
            
            # Step 5: Update conversation with analysis data
            if conversation.id:
                self.conversation_repo.update(conversation.id, update_data)
                
                # Update the conversation object with analysis data
                for key, value in update_data.items():
                    setattr(conversation, key, value)
                
                # Step 6: Generate and store embeddings for semantic search
                self._generate_and_store_embeddings(conversation)
            
            return conversation
            
        except Exception as e:
            logger.error(f"Error processing conversation: {e}")
            return conversation
    
    def _generate_and_store_embeddings(self, conversation: Conversation) -> None:
        """Generate and store embeddings for a conversation"""
        try:
            # Skip if conversation has no ID
            if not conversation.id:
                logger.warning("Cannot generate embeddings for conversation without ID")
                return
            
            # Delete any existing embeddings for this conversation
            self.embedding_repo.delete_by_conversation_id(conversation.id)
            
            # Get full text of conversation
            full_text = conversation.full_text()
            
            # Skip if conversation is empty
            if not full_text or len(full_text.strip()) == 0:
                logger.warning(f"Empty conversation text for ID: {conversation.id}")
                return
            
            # Chunk the text for embedding
            text_chunks = self.openai_service.chunk_text(full_text)
            
            # Generate embeddings for each chunk
            embeddings_list = []
            
            for i, chunk in enumerate(text_chunks):
                # Generate embedding
                embedding_vector = self.openai_service.generate_embedding(chunk)
                
                # Create ConversationEmbedding object
                embedding = ConversationEmbedding(
                    conversation_id=conversation.id,
                    conversation_title=conversation.title,
                    text_chunk=chunk,
                    embedding=embedding_vector,
                    chunk_index=i
                )
                
                embeddings_list.append(embedding)
            
            # Store embeddings in database
            if embeddings_list:
                self.embedding_repo.batch_create(embeddings_list)
                logger.info(f"Generated and stored {len(embeddings_list)} embeddings for conversation {conversation.id}")
        
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
    
    def find_related_conversations(self, conversation_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find conversations related to the given conversation"""
        try:
            # Get embeddings for the source conversation
            source_embeddings = self.embedding_repo.get_by_conversation_id(conversation_id)
            
            if not source_embeddings:
                logger.warning(f"No embeddings found for conversation {conversation_id}")
                return []
            
            # Use the first embedding as the query
            query_embedding = source_embeddings[0].embedding
            
            # Get all embeddings (inefficient for large datasets but simpler for now)
            all_embeddings = self.embedding_repo.get_all_embeddings(limit=1000)
            
            # Format for finding related topics
            formatted_embeddings = []
            for emb in all_embeddings:
                # Skip embeddings from the source conversation
                if emb.conversation_id != conversation_id:
                    formatted_embeddings.append((
                        emb.conversation_id,
                        emb.embedding,
                        emb.text_chunk
                    ))
            
            # Find related topics
            related = self.openai_service.find_related_topics(
                query_embedding, 
                formatted_embeddings,
                top_n=limit
            )
            
            # Enrich with conversation details
            enriched_results = []
            for item in related:
                conv = self.conversation_repo.get_by_id(item["conversation_id"])
                if conv:
                    enriched_results.append({
                        "conversation_id": item["conversation_id"],
                        "title": conv.title,
                        "similarity_score": item["similarity_score"],
                        "text_preview": item["text_preview"],
                        "created_at": conv.created_at
                    })
            
            return enriched_results
        
        except Exception as e:
            logger.error(f"Error finding related conversations: {e}")
            return []
    
    def search_conversations(self, user_id: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search conversations using semantic search"""
        try:
            # If query is very short, use traditional search
            if len(query) < 10:
                # Use basic text search
                conversations = self.conversation_repo.search(user_id, query, limit)
                return [
                    {
                        "conversation_id": conv.id,
                        "title": conv.title, 
                        "summary": conv.summary or "No summary available",
                        "created_at": conv.created_at,
                        "tags": conv.tags,
                        "categories": conv.categories
                    } 
                    for conv in conversations
                ]
            
            # For longer queries, use semantic search
            # Generate embedding for the query
            query_embedding = self.openai_service.generate_embedding(query)
            
            # Get all embeddings
            all_embeddings = self.embedding_repo.get_all_embeddings(limit=1000)
            
            # Filter embeddings by user_id (need to get conversation details)
            filtered_embeddings = []
            for emb in all_embeddings:
                # Get conversation to check user_id
                conv = self.conversation_repo.get_by_id(emb.conversation_id)
                if conv and conv.user_id == user_id:
                    filtered_embeddings.append((
                        emb.conversation_id,
                        emb.embedding,
                        emb.text_chunk
                    ))
            
            # Find semantically similar results
            results = self.openai_service.find_related_topics(
                query_embedding,
                filtered_embeddings,
                top_n=limit
            )
            
            # Enrich results with conversation details
            enriched_results = []
            seen_ids = set()  # To avoid duplicates
            
            for item in results:
                conv_id = item["conversation_id"]
                if conv_id not in seen_ids:
                    seen_ids.add(conv_id)
                    conv = self.conversation_repo.get_by_id(conv_id)
                    if conv:
                        enriched_results.append({
                            "conversation_id": conv_id,
                            "title": conv.title,
                            "summary": conv.summary or "No summary available",
                            "text_preview": item["text_preview"],
                            "similarity_score": item["similarity_score"],
                            "created_at": conv.created_at,
                            "tags": conv.tags,
                            "categories": conv.categories
                        })
            
            return enriched_results
        
        except Exception as e:
            logger.error(f"Error searching conversations: {e}")
            return []
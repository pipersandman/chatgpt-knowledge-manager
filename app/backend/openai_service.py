import logging
import json
from typing import List, Dict, Any, Optional, Tuple
import time

import openai
import numpy as np

from app.config.config import OPENAI_API_KEY, EMBEDDING_MODEL, GPT_MODEL
from app.models.conversation import Conversation, Message

# Configure logging
logger = logging.getLogger(__name__)

# Set OpenAI API key
openai.api_key = OPENAI_API_KEY

class OpenAIService:
    """Service for interacting with OpenAI API"""
    
    def __init__(self):
        if not OPENAI_API_KEY:
            logger.error("OpenAI API key not found")
            raise ValueError("OpenAI API key is required")
    
    def chat_completion(self, messages: List[Dict[str, str]], 
                        temperature: float = 0.7,
                        max_tokens: int = 1000) -> str:
        """Get a response from the chat model"""
        try:
            # Format messages for OpenAI API
            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Rate limiting to avoid API rate errors
            time.sleep(0.5)
            
            # Call OpenAI API
            response = openai.chat.completions.create(
                model=GPT_MODEL,
                messages=formatted_messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Return the model's response
            return response.choices[0].message.content
        
        except Exception as e:
            logger.error(f"Error calling OpenAI Chat API: {e}")
            return f"Error: Unable to get response from AI. {str(e)}"
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text"""
        try:
            # Rate limiting
            time.sleep(0.5)
            
            # Truncate text if it's too long
            # The exact limit depends on the model, but 8191 tokens is a safe upper bound for text-embedding-ada-002
            if len(text) > 30000:
                logger.warning(f"Truncating text of length {len(text)} for embedding")
                text = text[:30000]
            
            # Call OpenAI API
            response = openai.embeddings.create(
                model=EMBEDDING_MODEL,
                input=text
            )
            
            # Extract and return embedding
            embedding_vector = response.data[0].embedding
            return embedding_vector
        
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def batch_generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        embeddings = []
        
        for text in texts:
            try:
                embedding = self.generate_embedding(text)
                embeddings.append(embedding)
            except Exception as e:
                logger.error(f"Error generating embedding for text: {e}")
                # Add a placeholder embedding (zeros) if there's an error
                embeddings.append([0.0] * 1536)  # Ada embeddings are 1536-dimensional
        
        return embeddings
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks for embedding"""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            # Find the end of the chunk
            end = min(start + chunk_size, len(text))
            
            # If we're not at the end of the text, try to find a good break point
            if end < len(text):
                # Look for a period, question mark, or exclamation followed by a space
                punctuation_indices = [text.rfind(". ", start, end), 
                                      text.rfind("? ", start, end),
                                      text.rfind("! ", start, end)]
                
                # Find the latest punctuation (if any)
                latest_punctuation = max(punctuation_indices)
                
                if latest_punctuation != -1:
                    end = latest_punctuation + 2  # Include the punctuation and space
            
            # Add the chunk to our list
            chunks.append(text[start:end])
            
            # Move to next chunk, considering overlap
            start = end - overlap
        
        return chunks
    
    def analyze_conversation(self, conversation: Conversation) -> Dict[str, Any]:
        """Analyze a conversation to extract topics, summary, and key insights"""
        try:
            # Prepare the conversation text
            conversation_text = conversation.full_text()
            
            # Create a prompt for GPT to analyze the conversation
            prompt = f"""
            Please analyze the following conversation and extract the following information:
            1. A brief summary (2-3 sentences)
            2. Main topics discussed (comma-separated list)
            3. Key entities mentioned (people, companies, products, etc. as a comma-separated list)
            4. Important insights or decisions (bullet points)
            
            Format the response as a JSON object with the following keys:
            "summary", "topics", "entities", "insights"
            
            The conversation:
            {conversation_text}
            """
            
            # Get analysis from GPT
            analysis_text = self.chat_completion([
                {"role": "system", "content": "You are an AI that analyzes conversations and extracts structured information. Respond with JSON only."},
                {"role": "user", "content": prompt}
            ])
            
            # Parse the JSON response
            try:
                analysis = json.loads(analysis_text)
            except json.JSONDecodeError:
                logger.error("Failed to parse GPT analysis as JSON")
                # Attempt to extract information manually with a fallback approach
                analysis = {
                    "summary": "Unable to generate summary",
                    "topics": ["conversation"],
                    "entities": [],
                    "insights": ["Unable to extract insights"]
                }
            
            # Process the topics to create tags
            topics = analysis.get("topics", [])
            if isinstance(topics, str):
                # If topics is a string, split it by commas
                topics = [topic.strip() for topic in topics.split(",")]
            
            # Process entities
            entities = analysis.get("entities", [])
            if isinstance(entities, str):
                # If entities is a string, split it by commas
                entities = [entity.strip() for entity in entities.split(",")]
            
            # Process insights
            insights = analysis.get("insights", [])
            if isinstance(insights, str):
                # If insights is a string, split it by newlines or commas
                insights = [insight.strip() for insight in insights.replace("\n", ",").split(",")]
            
            # Return structured analysis
            return {
                "summary": analysis.get("summary", ""),
                "key_topics": topics,
                "extracted_entities": entities,
                "important_moments": [{"text": insight} for insight in insights]
            }
        
        except Exception as e:
            logger.error(f"Error analyzing conversation: {e}")
            return {
                "summary": "Error during analysis",
                "key_topics": [],
                "extracted_entities": [],
                "important_moments": []
            }
    
    def suggest_categories(self, conversation: Conversation, existing_categories: List[str]) -> List[str]:
        """Suggest appropriate categories for a conversation"""
        try:
            # Prepare conversation text
            conversation_text = conversation.full_text()
            
            # Create a prompt for GPT
            prompt = f"""
            Based on the following conversation, suggest 1-3 appropriate categories from this list:
            {', '.join(existing_categories)}
            
            If none of the existing categories fit well, you may suggest one new category.
            
            The conversation:
            {conversation_text[:5000]}  # First 5000 chars to keep prompt size reasonable
            
            Format your response as a comma-separated list of categories.
            """
            
            # Get suggestions from GPT
            categories_text = self.chat_completion([
                {"role": "system", "content": "You are an AI that categorizes conversations. Respond with only a comma-separated list of categories."},
                {"role": "user", "content": prompt}
            ])
            
            # Process the response
            suggested_categories = [cat.strip() for cat in categories_text.split(",")]
            
            # Return the suggested categories
            return suggested_categories
        
        except Exception as e:
            logger.error(f"Error suggesting categories: {e}")
            return []
    
    def find_related_topics(self, query_embedding: List[float], 
                            all_embeddings: List[Tuple[str, List[float], str]],
                            top_n: int = 5) -> List[Dict[str, Any]]:
        """Find related topics based on embedding similarity"""
        try:
            # Convert embeddings to numpy arrays for faster computation
            query_embedding_np = np.array(query_embedding)
            
            # Calculate similarity scores
            similarities = []
            for conv_id, embedding, text in all_embeddings:
                embedding_np = np.array(embedding)
                # Calculate cosine similarity
                similarity = np.dot(query_embedding_np, embedding_np) / (
                    np.linalg.norm(query_embedding_np) * np.linalg.norm(embedding_np)
                )
                similarities.append((conv_id, similarity, text))
            
            # Sort by similarity score (highest first)
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # Return top N results
            result = []
            seen_conv_ids = set()  # To avoid duplicates
            
            for conv_id, similarity, text in similarities[:top_n*2]:  # Get more than needed to filter duplicates
                if conv_id not in seen_conv_ids and len(result) < top_n:
                    seen_conv_ids.add(conv_id)
                    result.append({
                        "conversation_id": conv_id,
                        "similarity_score": float(similarity),
                        "text_preview": text[:200] + "..." if len(text) > 200 else text
                    })
            
            return result
        
        except Exception as e:
            logger.error(f"Error finding related topics: {e}")
            return []
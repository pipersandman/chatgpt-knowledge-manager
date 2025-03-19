import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Generator, Tuple
import time

from app.models.conversation import Conversation, Message
from app.database.conversation_repository import ConversationRepository
from app.backend.analysis_service import AnalysisService

# Configure logging
logger = logging.getLogger(__name__)

def stream_json_array(file_content: str) -> Generator[Dict[str, Any], None, None]:
    """
    Stream elements from a JSON array without loading the entire content into memory
    
    Args:
        file_content: JSON string containing an array of objects
        
    Yields:
        Individual objects from the JSON array
    """
    # First, validate the JSON starts with an array
    if not file_content.strip().startswith('['):
        raise ValueError("Expected JSON array starting with '['")
    
    # Skip the opening bracket
    content = file_content.strip()[1:]
    
    # Process array elements one at a time
    depth = 0
    start = 0
    in_string = False
    escape_next = False
    
    for i, char in enumerate(content):
        # Handle string boundary and escaping
        if char == '"' and not escape_next:
            in_string = not in_string
        
        # Track escape characters in strings
        if in_string and char == '\\':
            escape_next = not escape_next
        else:
            escape_next = False
        
        # Only track brackets outside of strings
        if not in_string:
            if char == '{':
                if depth == 0:
                    start = i
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    # We found a complete object
                    obj_str = content[start:i+1]
                    try:
                        obj = json.loads(obj_str)
                        yield obj
                    except json.JSONDecodeError:
                        logger.warning(f"Skipping invalid JSON object: {obj_str[:50]}...")
                    
                    # Skip any commas or whitespace to the next object
                    while i+1 < len(content) and content[i+1] in ', \n\r\t':
                        i += 1

def chunked_import(file_content: str, user_id: str, chunk_size: int = 10, 
                  callback=None) -> Dict[str, Any]:
    """
    Import conversations from a ChatGPT export in chunks to avoid memory issues
    
    Args:
        file_content: JSON string containing ChatGPT conversation export
        user_id: ID of the user who owns these conversations
        chunk_size: Number of conversations to process in each batch
        callback: Optional function to call with progress updates
        
    Returns:
        Dictionary with import results
    """
    try:
        # Initialize repositories and services
        conversation_repo = ConversationRepository()
        
        # Track import results
        results = {
            "total_processed": 0,
            "success": 0,
            "error": 0,
            "conversation_ids": [],
            "start_time": datetime.now(),
            "end_time": None,
            "duration_seconds": 0
        }
        
        # Create a generator to stream the JSON array
        conversations_stream = stream_json_array(file_content)
        
        # Process conversations in chunks
        chunk = []
        imported_count = 0
        
        for conv_data in conversations_stream:
            try:
                # Add to current chunk
                chunk.append(conv_data)
                
                # Process chunk if we've reached chunk_size
                if len(chunk) >= chunk_size:
                    process_chunk(chunk, user_id, conversation_repo, results)
                    
                    # Clear the chunk
                    chunk = []
                    
                    # Report progress if callback provided
                    imported_count += chunk_size
                    if callback:
                        callback(imported_count)
                    
                    # Small delay to avoid overwhelming the database
                    time.sleep(0.1)
            
            except Exception as e:
                logger.error(f"Error processing conversation in stream: {e}")
                results["error"] += 1
        
        # Process any remaining conversations in the final chunk
        if chunk:
            process_chunk(chunk, user_id, conversation_repo, results)
            if callback:
                callback(imported_count + len(chunk))
        
        # Calculate total duration
        results["end_time"] = datetime.now()
        results["duration_seconds"] = (results["end_time"] - results["start_time"]).total_seconds()
        
        return results
    
    except Exception as e:
        logger.error(f"Error during chunked import: {e}")
        return {
            "total_processed": 0,
            "success": 0,
            "error": 1,
            "error_message": str(e),
            "conversation_ids": []
        }

def process_chunk(chunk: List[Dict[str, Any]], user_id: str, 
                 conversation_repo: ConversationRepository, 
                 results: Dict[str, Any]) -> None:
    """
    Process a chunk of conversations
    
    Args:
        chunk: List of conversation data dictionaries
        user_id: User ID to assign to conversations
        conversation_repo: Repository for storing conversations
        results: Dictionary to update with results
    """
    # Process each conversation in the chunk
    for conv_data in chunk:
        try:
            # Extract conversation details
            conversation = parse_single_conversation(conv_data, user_id)
            
            # Skip invalid conversations
            if not conversation or not conversation.messages:
                results["error"] += 1
                results["total_processed"] += 1
                continue
            
            # Save to database
            conversation_id = conversation_repo.create(conversation)
            
            if conversation_id:
                results["success"] += 1
                results["conversation_ids"].append(conversation_id)
            else:
                results["error"] += 1
            
            results["total_processed"] += 1
        
        except Exception as e:
            logger.error(f"Error processing conversation in chunk: {e}")
            results["error"] += 1
            results["total_processed"] += 1

def parse_single_conversation(conv_data: Dict[str, Any], user_id: str) -> Optional[Conversation]:
    """
    Parse a single conversation from ChatGPT export format
    
    Args:
        conv_data: Dictionary containing conversation data
        user_id: User ID to assign to the conversation
        
    Returns:
        Conversation object or None if parsing failed
    """
    try:
        # Extract conversation metadata
        title = conv_data.get('title', 'Imported Conversation')
        
        # Extract messages
        raw_messages = conv_data.get('mapping', {})
        
        if not raw_messages:
            logger.warning(f"Skipping conversation '{title}' - no messages found")
            return None
        
        # Process messages
        messages = []
        
        # ChatGPT exports have a complex structure - find the message order
        message_order = []
        for node_id, node in raw_messages.items():
            if node.get('parent') is None and node.get('children'):
                # This is the root node, get its children to find the first message
                first_child_id = node.get('children', [])[0]
                message_order.append(first_child_id)
                break
        
        # Follow the message thread
        while message_order and message_order[-1] in raw_messages and 'children' in raw_messages[message_order[-1]]:
            children = raw_messages[message_order[-1]].get('children', [])
            if children:
                message_order.append(children[0])
            else:
                break
        
        # Extract messages in order
        for msg_id in message_order:
            if msg_id in raw_messages:
                node = raw_messages[msg_id]
                message = node.get('message', {})
                
                if message and 'content' in message:
                    content = message.get('content', {})
                    parts = content.get('parts', [])
                    text = ' '.join(parts) if parts else ''
                    
                    role = message.get('author', {}).get('role', 'user')
                    
                    # Skip system messages
                    if role == 'system':
                        continue
                    
                    # Create timestamp from create_time
                    create_time = message.get('create_time')
                    if create_time:
                        try:
                            timestamp = datetime.fromtimestamp(create_time)
                        except:
                            timestamp = datetime.utcnow()
                    else:
                        timestamp = datetime.utcnow()
                    
                    # Add message
                    if text and role in ['user', 'assistant']:
                        messages.append(Message(
                            role=role,
                            content=text,
                            timestamp=timestamp
                        ))
        
        # Skip conversations with no valid messages
        if not messages:
            logger.warning(f"Skipping conversation '{title}' - no valid messages found")
            return None
        
        # Create conversation object
        conversation = Conversation(
            user_id=user_id,
            title=title,
            messages=messages,
            created_at=messages[0].timestamp if messages else datetime.utcnow(),
            updated_at=messages[-1].timestamp if messages else datetime.utcnow()
        )
        
        return conversation
    
    except Exception as e:
        logger.error(f"Error parsing single conversation: {e}")
        return None

def analyze_conversations_background(conversation_ids: List[str]) -> None:
    """
    Analyze conversations in the background after import
    
    Args:
        conversation_ids: List of conversation IDs to analyze
    """
    try:
        # Initialize repositories and services
        conversation_repo = ConversationRepository()
        analysis_service = AnalysisService()
        
        # Process each conversation
        for conversation_id in conversation_ids:
            try:
                # Get the conversation
                conversation = conversation_repo.get_by_id(conversation_id)
                
                if conversation:
                    # Analyze conversation
                    analysis_service.process_new_conversation(conversation)
                    
                    # Small delay to avoid rate limits with OpenAI
                    time.sleep(0.5)
            
            except Exception as e:
                logger.error(f"Error analyzing conversation {conversation_id}: {e}")
    
    except Exception as e:
        logger.error(f"Error in background analysis: {e}")
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.models.conversation import Conversation, Message
from app.database.conversation_repository import ConversationRepository
from app.backend.analysis_service import AnalysisService

# Configure logging
logger = logging.getLogger(__name__)

def parse_chatgpt_export(file_content: str, user_id: str) -> List[Conversation]:
    """
    Parse a ChatGPT export file and convert to Conversation objects
    
    Args:
        file_content: JSON string containing ChatGPT conversation export
        user_id: ID of the user who owns these conversations
        
    Returns:
        List of Conversation objects parsed from the export
    """
    try:
        # Parse JSON
        data = json.loads(file_content)
        
        # Check if it's a valid ChatGPT export format
        if not isinstance(data, list):
            logger.error("Invalid ChatGPT export format - expected a list of conversations")
            raise ValueError("Invalid ChatGPT export format")
        
        # Initialize conversations list
        conversations = []
        
        # Process each conversation in the export
        for conv_data in data:
            try:
                # Extract conversation metadata
                title = conv_data.get('title', 'Imported Conversation')
                
                # Extract messages
                raw_messages = conv_data.get('mapping', {})
                
                if not raw_messages:
                    logger.warning(f"Skipping conversation '{title}' - no messages found")
                    continue
                
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
                while message_order[-1] in raw_messages and 'children' in raw_messages[message_order[-1]]:
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
                    continue
                
                # Create conversation object
                conversation = Conversation(
                    user_id=user_id,
                    title=title,
                    messages=messages,
                    created_at=messages[0].timestamp if messages else datetime.utcnow(),
                    updated_at=messages[-1].timestamp if messages else datetime.utcnow()
                )
                
                conversations.append(conversation)
            
            except Exception as e:
                logger.error(f"Error parsing conversation: {e}")
                # Continue to the next conversation
                continue
        
        return conversations
    
    except Exception as e:
        logger.error(f"Error parsing ChatGPT export: {e}")
        raise


def import_conversations(file_content: str, user_id: str) -> Dict[str, Any]:
    """
    Import conversations from a ChatGPT export file
    
    Args:
        file_content: JSON string containing ChatGPT conversation export
        user_id: ID of the user who owns these conversations
        
    Returns:
        Dictionary with import results (success count, error count)
    """
    try:
        # Initialize repositories and services
        conversation_repo = ConversationRepository()
        analysis_service = AnalysisService()
        
        # Parse conversations from export
        conversations = parse_chatgpt_export(file_content, user_id)
        
        # Track import results
        results = {
            "total": len(conversations),
            "success": 0,
            "error": 0,
            "conversation_ids": []
        }
        
        # Import each conversation
        for conversation in conversations:
            try:
                # Save conversation to database
                conversation_id = conversation_repo.create(conversation)
                
                if conversation_id:
                    # Update conversation ID
                    conversation.id = conversation_id
                    results["conversation_ids"].append(conversation_id)
                    
                    # Analyze conversation
                    analysis_service.process_new_conversation(conversation)
                    
                    results["success"] += 1
                else:
                    results["error"] += 1
            
            except Exception as e:
                logger.error(f"Error importing conversation: {e}")
                results["error"] += 1
        
        return results
    
    except Exception as e:
        logger.error(f"Error during import: {e}")
        return {
            "total": 0,
            "success": 0,
            "error": 1,
            "error_message": str(e)
        }
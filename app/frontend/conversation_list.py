import streamlit as st
import logging
from datetime import datetime

from app.utils.session import get_current_user
from app.database.conversation_repository import ConversationRepository

# Configure logging
logger = logging.getLogger(__name__)

def show_conversation_list():
    """Display a list of all conversations with filtering options"""
    try:
        st.title("All Conversations")
        
        # Get current user
        user = get_current_user()
        if not user:
            st.warning("User session expired. Please log in again.")
            return
        
        # Initialize repository
        conversation_repo = ConversationRepository()
        
        # Get all categories and tags for filtering
        categories = conversation_repo.get_all_categories(user["id"])
        tags = conversation_repo.get_all_tags(user["id"])
        
        # Add 'All' option
        categories = ["All Categories"] + categories
        tags = ["All Tags"] + tags
        
        # Create filter UI
        col1, col2, col3 = st.columns(3)
        
        with col1:
            selected_category = st.selectbox("Filter by Category", categories)
        
        with col2:
            selected_tag = st.selectbox("Filter by Tag", tags)
        
        with col3:
            sort_options = ["Most Recent", "Oldest First", "Alphabetically"]
            sort_option = st.selectbox("Sort by", sort_options)
        
        # Fetch conversations based on filters
        if selected_category == "All Categories" and selected_tag == "All Tags":
            # Get all conversations
            conversations = conversation_repo.get_by_user(user["id"])
        elif selected_category != "All Categories" and selected_tag == "All Tags":
            # Filter by category
            conversations = conversation_repo.filter_by_category(user["id"], selected_category)
        elif selected_category == "All Categories" and selected_tag != "All Tags":
            # Filter by tag
            conversations = conversation_repo.filter_by_tag(user["id"], selected_tag)
        else:
            # Get conversations that have both the selected category and tag
            category_conversations = conversation_repo.filter_by_category(user["id"], selected_category)
            conversations = [c for c in category_conversations if selected_tag in c.tags]
        
        # Sort conversations
        if sort_option == "Most Recent":
            conversations.sort(key=lambda x: x.updated_at, reverse=True)
        elif sort_option == "Oldest First":
            conversations.sort(key=lambda x: x.updated_at)
        elif sort_option == "Alphabetically":
            conversations.sort(key=lambda x: x.title)
        
        # Display conversation count
        st.write(f"Showing {len(conversations)} conversations")
        
        if not conversations:
            st.info("No conversations found with the selected filters.")
        else:
            # Display conversations
            for conv in conversations:
                show_conversation_item(conv)
    
    except Exception as e:
        logger.error(f"Error displaying conversation list: {e}")
        st.error(f"An error occurred: {str(e)}")


def show_conversation_item(conversation):
    """Display a single conversation item with actions"""
    with st.container():
        col1, col2 = st.columns([4, 1])
        
        with col1:
            # Format dates
            created_date = conversation.created_at.strftime("%b %d, %Y")
            updated_date = conversation.updated_at.strftime("%b %d, %Y")
            
            # Create expandable container
            with st.expander(conversation.title):
                # Show summary if available
                if conversation.summary:
                    st.write("Summary:")
                    st.write(conversation.summary)
                
                # Show metadata
                st.write(f"Created: {created_date}")
                st.write(f"Last Updated: {updated_date}")
                
                # Show categories
                if conversation.categories:
                    st.write("Categories:")
                    category_html = " ".join([f'<span class="category">{cat}</span>' for cat in conversation.categories])
                    st.markdown(category_html, unsafe_allow_html=True)
                
                # Show tags
                if conversation.tags:
                    st.write("Tags:")
                    tag_html = " ".join([f'<span class="tag">{tag}</span>' for tag in conversation.tags])
                    st.markdown(tag_html, unsafe_allow_html=True)
                
                # Show first few messages as preview
                if conversation.messages:
                    st.write("Preview:")
                    messages_preview = conversation.messages[:2]  # Show first 2 messages
                    
                    for msg in messages_preview:
                        role = "You" if msg.role == "user" else "Assistant"
                        
                        # Truncate message content if too long
                        content = msg.content
                        if len(content) > 200:
                            content = content[:200] + "..."
                        
                        if msg.role == "user":
                            st.markdown(f'<div class="user-message"><strong>{role}:</strong> {content}</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="assistant-message"><strong>{role}:</strong> {content}</div>', unsafe_allow_html=True)
        
        with col2:
            st.button("View", key=f"view_{conversation.id}", 
                     on_click=view_conversation, args=(conversation.id,))


def view_conversation(conversation_id):
    """Set session state to view a conversation"""
    st.session_state.view_conversation = True
    st.session_state.conversation_id = conversation_id
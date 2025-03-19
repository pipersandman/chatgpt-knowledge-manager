import streamlit as st
import logging
from datetime import datetime

from app.utils.session import get_current_user
from app.database.conversation_repository import ConversationRepository
from app.backend.analysis_service import AnalysisService

# Configure logging
logger = logging.getLogger(__name__)

def show_conversation_view(conversation_id):
    """Display a single conversation with its messages and analysis"""
    try:
        # Create repositories and services
        conversation_repo = ConversationRepository()
        analysis_service = AnalysisService()
        
        # Get conversation
        conversation = conversation_repo.get_by_id(conversation_id)
        
        if not conversation:
            st.error("Conversation not found")
            close_conversation_view()
            return
        
        # Check if user has access to this conversation
        user = get_current_user()
        if not user or conversation.user_id != user["id"]:
            st.error("You don't have permission to view this conversation")
            close_conversation_view()
            return
        
        # Create back button and header
        col1, col2 = st.columns([1, 3])
        
        with col1:
            if st.button("← Back"):
                close_conversation_view()
                return
        
        with col2:
            st.title(conversation.title)
        
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["Conversation", "Analysis", "Related Content"])
        
        # Tab 1: Conversation content
        with tab1:
            # Display metadata in a card
            with st.container():
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"Created: {conversation.created_at.strftime('%b %d, %Y')}")
                    st.write(f"Updated: {conversation.updated_at.strftime('%b %d, %Y')}")
                
                with col2:
                    # Display categories
                    if conversation.categories:
                        st.write("Categories:")
                        category_html = " ".join([f'<span class="category">{cat}</span>' for cat in conversation.categories])
                        st.markdown(category_html, unsafe_allow_html=True)
                    
                    # Display tags
                    if conversation.tags:
                        st.write("Tags:")
                        tag_html = " ".join([f'<span class="tag">{tag}</span>' for tag in conversation.tags])
                        st.markdown(tag_html, unsafe_allow_html=True)
            
            st.divider()
            
            # Display messages
            if not conversation.messages:
                st.info("This conversation doesn't have any messages.")
            else:
                for msg in conversation.messages:
                    role = "You" if msg.role == "user" else "Assistant"
                    
                    if msg.role == "user":
                        st.markdown(f'<div class="user-message"><strong>{role}:</strong> {msg.content}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="assistant-message"><strong>{role}:</strong> {msg.content}</div>', unsafe_allow_html=True)
        
        # Tab 2: Analysis of the conversation
        with tab2:
            # Show summary
            st.subheader("Summary")
            if conversation.summary:
                st.write(conversation.summary)
            else:
                if st.button("Generate Summary"):
                    with st.spinner("Analyzing conversation..."):
                        # Process conversation with AI analysis
                        updated_conv = analysis_service.process_new_conversation(conversation)
                        st.success("Analysis complete!")
                        st.rerun()  # Refresh to show new analysis
            
            # Show topics
            st.subheader("Key Topics")
            if conversation.key_topics:
                topic_html = " ".join([f'<span class="tag">{topic}</span>' for topic in conversation.key_topics])
                st.markdown(topic_html, unsafe_allow_html=True)
            else:
                st.write("No topics identified yet.")
            
            # Show entities
            if conversation.extracted_entities:
                st.subheader("Entities Mentioned")
                entity_html = " ".join([f'<span class="tag">{entity}</span>' for entity in conversation.extracted_entities])
                st.markdown(entity_html, unsafe_allow_html=True)
            
            # Show important moments
            if conversation.important_moments:
                st.subheader("Key Insights")
                for moment in conversation.important_moments:
                    st.markdown(f'<div class="insight-item">{moment["text"]}</div>', unsafe_allow_html=True)
        
        # Tab 3: Related content
        with tab3:
            st.subheader("Related Conversations")
            
            # Find related conversations
            related = analysis_service.find_related_conversations(conversation_id)
            
            if not related:
                st.info("No related conversations found. This might be because embeddings haven't been generated yet.")
                
                if st.button("Generate Embeddings"):
                    with st.spinner("Generating embeddings for semantic search..."):
                        # Process conversation to generate embeddings
                        analysis_service.process_new_conversation(conversation)
                        st.success("Embeddings generated successfully!")
                        st.rerun()
            else:
                # Display related conversations
                for item in related:
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        st.markdown(f"**{item['title']}**")
                        st.write(f"Similarity: {item['similarity_score']:.2f}")
                        st.write(item['text_preview'])
                    
                    with col2:
                        st.button("View", key=f"related_{item['conversation_id']}", 
                                 on_click=view_related_conversation, 
                                 args=(item['conversation_id'],))
    
    except Exception as e:
        logger.error(f"Error displaying conversation: {e}")
        st.error(f"An error occurred: {str(e)}")


def close_conversation_view():
    """Close the conversation view and return to previous page"""
    st.session_state.view_conversation = False
    st.session_state.conversation_id = None


def view_related_conversation(conversation_id):
    """View a related conversation"""
    st.session_state.conversation_id = conversation_id
    st.rerun()

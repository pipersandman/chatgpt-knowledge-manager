import streamlit as st
import logging
from datetime import datetime
import pandas as pd
import plotly.express as px

from app.utils.session import get_current_user
from app.database.conversation_repository import ConversationRepository
from app.backend.analysis_service import AnalysisService

# Configure logging
logger = logging.getLogger(__name__)

def show_dashboard():
    """Display the dashboard with stats and recent conversations"""
    try:
        st.title("Dashboard")
        
        # Get current user
        user = get_current_user()
        if not user:
            st.warning("User session expired. Please log in again.")
            return
        
        # Initialize repositories and services
        conversation_repo = ConversationRepository()
        analysis_service = AnalysisService()
        
        # Create layout with columns
        col1, col2, col3 = st.columns(3)
        
        # Get user's conversations
        conversations = conversation_repo.get_by_user(user["id"])
        
        # Stat 1: Total Conversations
        with col1:
            show_stat_card("Total Conversations", len(conversations), "📚")
        
        # Stat 2: Categories
        all_categories = conversation_repo.get_all_categories(user["id"])
        with col2:
            show_stat_card("Categories", len(all_categories), "🏷️")
        
        # Stat 3: Tags
        all_tags = conversation_repo.get_all_tags(user["id"])
        with col3:
            show_stat_card("Tags", len(all_tags), "🔖")
        
        # Recent activity section
        st.subheader("Recent Conversations")
        
        if not conversations:
            st.info("You don't have any conversations yet. Start by importing your chat history.")
        else:
            recent_conversations = conversations[:5]  # Display 5 most recent
            
            for conv in recent_conversations:
                with st.container():
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        show_conversation_card(conv)
                    
                    with col2:
                        st.button("View", key=f"view_{conv.id}", 
                                 on_click=view_conversation, args=(conv.id,))
        
        # Conversation activity over time
        if conversations:
            st.subheader("Conversation Activity")
            
            # Prepare data for chart
            dates = [conv.created_at.date() for conv in conversations]
            date_counts = pd.Series(dates).value_counts().sort_index()
            date_df = pd.DataFrame({
                'Date': date_counts.index,
                'Count': date_counts.values
            })
            
            # Create the chart
            fig = px.line(date_df, x='Date', y='Count', 
                          title='Conversations Over Time',
                          labels={'Count': 'Number of Conversations', 'Date': 'Date'})
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        # Popular topics section
        if all_tags:
            st.subheader("Popular Topics")
            
            # Count occurrences of each tag
            tag_counts = {}
            for conv in conversations:
                for tag in conv.tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            # Sort tags by count
            sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
            top_tags = sorted_tags[:10]  # Display top 10 tags
            
            # Create a bar chart
            tag_df = pd.DataFrame(top_tags, columns=['Tag', 'Count'])
            fig = px.bar(tag_df, x='Tag', y='Count', 
                         title='Most Used Tags',
                         labels={'Count': 'Number of Uses', 'Tag': 'Tag'})
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        logger.error(f"Error displaying dashboard: {e}")
        st.error(f"An error occurred: {str(e)}")


def show_stat_card(title, value, emoji):
    """Display a statistics card"""
    st.markdown(f"""
    <div class="stat-card">
        <div>{emoji}</div>
        <div class="stat-number">{value}</div>
        <div class="stat-label">{title}</div>
    </div>
    """, unsafe_allow_html=True)


def show_conversation_card(conversation):
    """Display a conversation card with title and metadata"""
    # Format date
    date_str = conversation.updated_at.strftime("%b %d, %Y")
    
    # Get tags as string
    tags = ", ".join(conversation.tags) if conversation.tags else "No tags"
    
    # Create card
    st.markdown(f"""
    <div class="conversation-card">
        <div class="conversation-title">{conversation.title}</div>
        <div class="conversation-meta">Last updated: {date_str}</div>
        <div class="conversation-meta">Tags: {tags}</div>
    </div>
    """, unsafe_allow_html=True)


def view_conversation(conversation_id):
    """Set session state to view a conversation"""
    st.session_state.view_conversation = True
    st.session_state.conversation_id = conversation_id
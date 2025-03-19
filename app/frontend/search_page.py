import streamlit as st
import logging
from datetime import datetime

from app.utils.session import get_current_user
from app.backend.analysis_service import AnalysisService

# Configure logging
logger = logging.getLogger(__name__)

def show_search_page():
    """Display search interface with semantic search capabilities"""
    try:
        st.title("Search Conversations")
        
        # Get current user
        user = get_current_user()
        if not user:
            st.warning("User session expired. Please log in again.")
            return
        
        # Initialize services
        analysis_service = AnalysisService()
        
        # Create search interface
        st.write("Search your conversations using AI-powered semantic search")
        
        # Search input with placeholder
        query = st.text_input("Enter your search query:", 
                            placeholder="Try searching for topics, concepts, or specific questions...")
        
        # Advanced search options
        with st.expander("Advanced Search Options"):
            col1, col2 = st.columns(2)
            
            with col1:
                search_mode = st.radio("Search Mode", 
                                    ["Semantic Search", "Keyword Search"],
                                    help="Semantic search finds related concepts even if exact words don't match")
            
            with col2:
                result_limit = st.slider("Maximum Results", 
                                        min_value=5, 
                                        max_value=50, 
                                        value=10,
                                        help="Maximum number of results to display")
        
        # Process search when query is entered
        if query:
            with st.spinner(f"Searching for '{query}'..."):
                # Perform search using semantic search or keyword search based on mode
                search_results = analysis_service.search_conversations(
                    user_id=user["id"],
                    query=query,
                    limit=result_limit
                )
                
                # Show results
                st.subheader(f"Search Results ({len(search_results)} found)")
                
                if not search_results:
                    st.info("No matching conversations found.")
                else:
                    # Display results
                    for i, result in enumerate(search_results):
                        show_search_result(result, i+1)
        
        # Placeholder content when no search is performed
        if not query:
            st.info("Enter a search query to find conversations.")
            
            # Show sample queries as suggestions
            st.subheader("Sample Queries")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                - AI ethics and safety
                - Project planning methodology
                - Data visualization techniques
                """)
            
            with col2:
                st.markdown("""
                - Creative writing tips
                - Machine learning models
                - Career advice
                """)
    
    except Exception as e:
        logger.error(f"Error displaying search page: {e}")
        st.error(f"An error occurred: {str(e)}")


def show_search_result(result, index):
    """Display a single search result with contextual info"""
    with st.container():
        # Header with title and similarity score if available
        header_col1, header_col2 = st.columns([4, 1])
        
        with header_col1:
            st.subheader(f"{index}. {result['title']}")
        
        with header_col2:
            if 'similarity_score' in result:
                score = result['similarity_score'] * 100
                st.write(f"Match: {score:.0f}%")
        
        # Show snippet or summary
        if 'text_preview' in result and result['text_preview']:
            st.markdown(f"**Snippet:** _{result['text_preview']}_")
        elif 'summary' in result and result['summary']:
            st.markdown(f"**Summary:** _{result['summary']}_")
        
        # Show metadata
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            if 'created_at' in result and result['created_at']:
                date_str = result['created_at'].strftime("%b %d, %Y")
                st.write(f"Created: {date_str}")
        
        with col2:
            # Show tags
            if 'tags' in result and result['tags']:
                tag_html = " ".join([f'<span class="tag">{tag}</span>' for tag in result['tags'][:3]])
                st.markdown(f"Tags: {tag_html}", unsafe_allow_html=True)
        
        with col3:
            # View button
            st.button("View", key=f"search_result_{result['conversation_id']}", 
                     on_click=view_conversation, args=(result['conversation_id'],))
        
        # Divider between results
        st.divider()


def view_conversation(conversation_id):
    """Set session state to view a conversation"""
    st.session_state.view_conversation = True
    st.session_state.conversation_id = conversation_id
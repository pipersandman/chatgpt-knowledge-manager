import streamlit as st
import os
import logging
import traceback
from pathlib import Path
import os
import subprocess

# Attempt to install FAISS only if not already installed
try:
    import faiss
except ImportError:
    subprocess.run(["pip", "install", "faiss-cpu"], check=True)
    import faiss  # Now try importing again


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import app modules
try:
    from app.config.config import APP_NAME
    from app.utils.session import init_session_state, get_current_user
    from app.frontend.login_page import show_login_page
    from app.frontend.dashboard import show_dashboard
    from app.frontend.conversation_list import show_conversation_list
    from app.frontend.conversation_view import show_conversation_view
    from app.frontend.search_page import show_search_page
    from app.frontend.topic_map import show_topic_map
    from app.frontend.settings_page import show_settings
    print("All imports successful")
except Exception as e:
    logger.error(f"Import error: {e}")
    print(f"Import error: {e}")
    traceback.print_exc()

def main():
    """Main application entry point"""
    try:
        # Set up page config
        st.set_page_config(
            page_title=APP_NAME,
            page_icon="🧠",
            layout="wide"
        )
        
        # Debug message to confirm execution
        print("Application starting...")
        
        # Initialize session state
        init_session_state()
        print("Session state initialized")
        
        # Custom CSS
        try:
            css_path = Path(__file__).parent / "app" / "frontend" / "static" / "style.css"
            print(f"Looking for CSS at: {css_path}")
            if css_path.exists():
                with open(css_path) as f:
                    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
                    print("CSS loaded successfully")
            else:
                print(f"CSS file not found at {css_path}")
        except Exception as css_error:
            print(f"Error loading CSS: {css_error}")
        
        # Check if user is logged in
        user = get_current_user()
        print(f"Current user: {user}")
        
        # Display login page if not authenticated
        if not user:
            print("Showing login page")
            show_login_page()
            return
        
        # User is authenticated, show sidebar and content
        with st.sidebar:
            st.title(f"🧠 {APP_NAME}")
            
            # User info
            st.write(f"Welcome, {user['name']}")
            
            # Navigation
            st.subheader("Navigation")
            
            # Define pages
            pages = {
                "Dashboard": show_dashboard,
                "All Conversations": show_conversation_list,
                "Search": show_search_page,
                "Topic Map": show_topic_map,
                "Settings": show_settings
            }
            
            # Page selection
            selection = st.radio("Go to", list(pages.keys()))
            
            # Logout button
            if st.button("Logout"):
                from app.utils.session import logout_user
                logout_user()
                st.experimental_rerun()
        
        # Show selected page
        if 'view_conversation' in st.session_state and st.session_state.view_conversation:
            show_conversation_view(st.session_state.conversation_id)
        else:
            pages[selection]()
    
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        st.error(f"An error occurred: {str(e)}")
        print(f"Application error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
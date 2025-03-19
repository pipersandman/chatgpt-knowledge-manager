import streamlit as st
import logging
import traceback
import subprocess
import sys
import os
from pathlib import Path

# Import environment variables
from app.config.config import MONGODB_URI, MONGODB_DB_NAME, APP_NAME
from app.utils.session import init_session_state, get_current_user
from app.frontend.login_page import show_login_page
from app.frontend.dashboard import show_dashboard
from app.frontend.conversation_list import show_conversation_list
from app.frontend.conversation_view import show_conversation_view
from app.frontend.search_page import show_search_page
from app.frontend.topic_map import show_topic_map
from app.frontend.settings_page import show_settings

# Ensure FAISS is installed dynamically
try:
    import faiss
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "--no-cache-dir", "faiss-cpu"], check=True)
    import faiss  # Import again after installation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Database Connection (Ensuring it's set up correctly)
from pymongo import MongoClient

# Ensure MongoDB credentials are set
if not MONGODB_URI:
    raise ValueError("⚠️ MONGODB_URI is missing from .env file!")
if not MONGODB_DB_NAME:
    raise ValueError("⚠️ MONGODB_DB_NAME is missing from .env file!")

try:
    # Connect to MongoDB
    client = MongoClient(MONGODB_URI)

    # Verify connection by pinging the server
    client.admin.command("ping")

    # Get the database instance
    db = client[MONGODB_DB_NAME]

    logger.info(f"✅ Successfully connected to MongoDB: {MONGODB_DB_NAME}")

except Exception as e:
    logger.error(f"❌ MongoDB Connection Failed: {e}")
    raise ConnectionError(f"❌ MongoDB Connection Failed: {e}")

def main():
    """Main application entry point"""
    try:
        # Set up page config
        st.set_page_config(
            page_title=APP_NAME,
            page_icon="🧠",
            layout="wide"
        )

        # Debugging information
        print("🚀 Application Starting...")
        
        # Initialize session state (only inside the main function)
        init_session_state()
        print("✅ Session state initialized")

        # Custom CSS
        try:
            css_path = Path(__file__).parent / "app" / "frontend" / "static" / "style.css"
            if css_path.exists():
                with open(css_path) as f:
                    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
                print("🎨 CSS Loaded Successfully")
            else:
                print(f"⚠️ CSS file not found at {css_path}")
        except Exception as css_error:
            print(f"⚠️ Error loading CSS: {css_error}")

        # Check if user is logged in
        user = get_current_user()
        print(f"👤 Current user: {user}")

        # Display login page if not authenticated
        if not user:
            print("🔑 Showing login page")
            show_login_page()
            return

        # User is authenticated, show sidebar and content
        with st.sidebar:
            st.title(f"🧠 {APP_NAME}")
            st.write(f"Welcome, {user['name']}")

            # Navigation
            st.subheader("Navigation")
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
        if "view_conversation" in st.session_state and st.session_state.view_conversation:
            show_conversation_view(st.session_state.conversation_id)
        else:
            pages[selection]()

    except Exception as e:
        logger.error(f"❌ Application error: {e}", exc_info=True)
        st.error(f"An error occurred: {str(e)}")
        print(f"❌ Application error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()

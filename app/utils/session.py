import logging
from typing import Dict, Optional, Any
from datetime import datetime, timedelta

import streamlit as st
from app.utils.auth import authenticate_user, create_access_token
from app.database.user_repository import UserRepository

# Configure logging
logger = logging.getLogger(__name__)

def init_session_state():
    """Initialize session state variables for authentication"""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None
    if 'user_name' not in st.session_state:
        st.session_state.user_name = None
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'auth_token' not in st.session_state:
        st.session_state.auth_token = None
    if 'login_error' not in st.session_state:
        st.session_state.login_error = None


def login_user(email: str, password: str) -> bool:
    """Login a user and set session state"""
    try:
        user = authenticate_user(email, password)
        
        if not user:
            st.session_state.login_error = "Invalid email or password"
            return False
        
        # Create access token
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id}
        )
        
        # Set session state
        st.session_state.user_id = user.id
        st.session_state.user_email = user.email
        st.session_state.user_name = user.name
        st.session_state.authenticated = True
        st.session_state.auth_token = access_token
        st.session_state.login_error = None
        
        logger.info(f"User {user.email} logged in successfully")
        return True
    
    except Exception as e:
        logger.error(f"Login error: {e}")
        st.session_state.login_error = "An error occurred during login"
        return False


def logout_user():
    """Logout user and clear session state"""
    # Clear session state
    st.session_state.user_id = None
    st.session_state.user_email = None
    st.session_state.user_name = None
    st.session_state.authenticated = False
    st.session_state.auth_token = None
    st.session_state.login_error = None
    
    logger.info("User logged out")


def get_current_user() -> Optional[Dict[str, Any]]:
    """Get information about the currently logged in user"""
    if not st.session_state.authenticated or not st.session_state.user_id:
        return None
    
    try:
        user_repo = UserRepository()
        user = user_repo.get_by_id(st.session_state.user_id)
        
        if not user:
            # Session exists but user not found in database
            logout_user()
            return None
        
        return {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "custom_categories": user.custom_categories,
            "favorite_tags": user.favorite_tags,
            "ui_preferences": user.ui_preferences
        }
    except Exception as e:
        logger.error(f"Error retrieving current user: {e}")
        return None


def check_authentication():
    """Check if user is authenticated, redirect to login if not"""
    init_session_state()
    
    if not st.session_state.authenticated:
        st.warning("Please log in to access this page")
        st.stop()
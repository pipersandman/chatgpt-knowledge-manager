import streamlit as st
import logging

from app.utils.auth import get_password_hash
from app.utils.session import login_user
from app.models.user import User, UserCreate
from app.database.user_repository import UserRepository

# Configure logging
logger = logging.getLogger(__name__)

def show_login_page():
    """Display the login page with login and registration forms"""
    
    st.title("🧠 AI Knowledge Manager")
    
    # Create tabs for login and registration
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    # Login tab
    with tab1:
        st.subheader("Login")
        
        # Show error message if login failed
        if st.session_state.get('login_error'):
            st.error(st.session_state.login_error)
        
        # Login form
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submit_button = st.form_submit_button("Login")
            
            if submit_button:
                if not email or not password:
                    st.error("Please enter both email and password")
                else:
                    if login_user(email, password):
                        st.rerun()
    
    # Registration tab
    with tab2:
        st.subheader("Create an Account")
        
        # Registration form
        with st.form("register_form"):
            name = st.text_input("Full Name", key="register_name")
            email = st.text_input("Email", key="register_email")
            password = st.text_input("Password", type="password", key="register_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="register_confirm")
            
            submit_button = st.form_submit_button("Register")
            
            if submit_button:
                if not name or not email or not password:
                    st.error("Please fill out all fields")
                elif password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    if register_user(name, email, password):
                        st.success("Registration successful! You can now log in.")
                        # Remove form values from session state
                        st.session_state.pop("register_name", None)
                        st.session_state.pop("register_email", None)
                        st.session_state.pop("register_password", None)
                        st.session_state.pop("register_confirm", None)
                        st.rerun()

def register_user(name: str, email: str, password: str) -> bool:
    """Register a new user in the database"""
    try:
        user_repo = UserRepository()
        
        # Check if user already exists
        existing_user = user_repo.get_by_email(email)
        if existing_user:
            st.error("A user with this email already exists.")
            return False
        
        # Hash the password
        hashed_password = get_password_hash(password)
        
        # Create user model
        user = User(
            email=email,
            hashed_password=hashed_password,
            name=name
        )
        
        # Store in database
        user_id = user_repo.create(user)
        
        if not user_id:
            st.error("Failed to create user.")
            return False
        
        logger.info(f"Created new user with email: {email}")
        return True
    
    except Exception as e:
        logger.error(f"Registration error: {e}")
        st.error(f"An error occurred during registration: {str(e)}")
        return False
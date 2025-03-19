import streamlit as st
import sys
import traceback
import os
from pathlib import Path

st.set_page_config(page_title="Diagnostics", layout="wide")
st.title("Application Diagnostics")

# Check Python version
st.write(f"Python version: {sys.version}")

# Check file structure
root_dir = Path(".")
st.write("### File Structure Check")
dirs_to_check = ["app", "app/config", "app/utils", "app/frontend", "app/models", "app/database", "app/backend"]
for dir_path in dirs_to_check:
    path = root_dir / dir_path
    if path.exists():
        st.success(f"✓ {dir_path} directory exists")
    else:
        st.error(f"✗ {dir_path} directory missing")

# Check for __init__.py files
st.write("### Package Structure Check")
for dir_path in dirs_to_check:
    path = root_dir / dir_path / "__init__.py"
    if path.exists():
        st.success(f"✓ {dir_path}/__init__.py exists")
    else:
        st.error(f"✗ {dir_path}/__init__.py missing")

# Check crucial files
st.write("### Critical Files Check")
critical_files = [
    "app/config/config.py",
    "app/utils/session.py",
    "app/frontend/login_page.py"
]
for file_path in critical_files:
    path = root_dir / file_path
    if path.exists():
        st.success(f"✓ {file_path} exists")
    else:
        st.error(f"✗ {file_path} missing")

# Check .env file
st.write("### Environment Check")
env_path = root_dir / ".env"
if env_path.exists():
    st.success("✓ .env file exists")
    
    # Try to load .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
        st.success("✓ .env file loaded successfully")
        
        # Check mandatory environment variables
        env_vars = ["MONGODB_URI", "MONGODB_DB_NAME", "SECRET_KEY", "OPENAI_API_KEY"]
        for var in env_vars:
            if os.getenv(var):
                st.success(f"✓ {var} is set")
            else:
                st.error(f"✗ {var} is not set")
    except Exception as e:
        st.error(f"✗ Error loading .env: {e}")
else:
    st.error("✗ .env file missing")

# Check MongoDB connection
st.write("### MongoDB Connection Check")
try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure
    
    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGODB_DB_NAME", "knowledge_manager")
    
    st.info(f"Attempting to connect to MongoDB: {uri}")
    
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    
    st.success(f"✓ Connected to MongoDB server")
    
    # Check database and collections
    db = client[db_name]
    collections = db.list_collection_names()
    
    st.success(f"✓ Found database: {db_name}")
    st.write(f"Collections: {collections}")
    
except ConnectionFailure as e:
    st.error(f"✗ MongoDB connection failed: {e}")
except Exception as e:
    st.error(f"✗ MongoDB error: {e}")
    st.code(traceback.format_exc())

# Try to import app modules
st.write("### Application Module Imports")
modules_to_check = [
    "app.config.config",
    "app.utils.session",
    "app.frontend.login_page",
    "app.frontend.dashboard",
    "app.database.connection",
    "app.backend.openai_service"
]

for module in modules_to_check:
    try:
        __import__(module)
        st.success(f"✓ Successfully imported {module}")
    except Exception as e:
        st.error(f"✗ Failed to import {module}: {e}")
        with st.expander("Traceback"):
            st.code(traceback.format_exc())
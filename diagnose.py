import streamlit as st
import sys
import traceback
import os
from pathlib import Path
from dotenv import load_dotenv

st.set_page_config(page_title="Diagnostics", layout="wide")
st.title("Application Diagnostics")

# Load .env variables
env_path = Path(".env")
if env_path.exists():
    load_dotenv()
    st.success("✓ .env file loaded successfully")
else:
    st.error("✗ .env file missing!")

# Ensure required environment variables exist
env_vars = ["MONGODB_URI", "MONGODB_DB_NAME", "SECRET_KEY", "OPENAI_API_KEY"]
missing_vars = [var for var in env_vars if not os.getenv(var)]

if missing_vars:
    for var in missing_vars:
        st.error(f"✗ {var} is NOT set in .env!")
else:
    for var in env_vars:
        st.success(f"✓ {var} is set")

# Get MongoDB credentials
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME")

# MongoDB Connection Check
st.write("### MongoDB Connection Check")

if not MONGODB_URI or not MONGODB_DB_NAME:
    st.error("❌ MongoDB credentials are missing in the .env file!")
else:
    try:
        from pymongo import MongoClient
        from pymongo.errors import ConnectionFailure, OperationFailure

        st.info(f"🔍 Attempting to connect to MongoDB: `{MONGODB_URI}`")

        # Initialize MongoDB Client with a 10s timeout
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=10000)

        # Test connection
        client.admin.command("ping")
        st.success("✅ Successfully connected to MongoDB server!")

        # Check if the database exists
        db = client[MONGODB_DB_NAME]
        collections = db.list_collection_names()

        st.success(f"✅ Found database: `{MONGODB_DB_NAME}`")
        st.write(f"📂 Collections in `{MONGODB_DB_NAME}`: {collections}")

    except ConnectionFailure:
        st.error("❌ MongoDB connection failed! Unable to reach the server.")
    except OperationFailure as e:
        st.error("❌ Authentication Failed: Check your MongoDB username and password!")
        st.code(str(e))
    except Exception as e:
        st.error(f"❌ Unknown MongoDB error: {e}")
        st.code(traceback.format_exc())

# Application Structure Check
st.write("### File Structure Check")
dirs_to_check = [
    "app",
    "app/config",
    "app/utils",
    "app/frontend",
    "app/models",
    "app/database",
    "app/backend"
]
for dir_path in dirs_to_check:
    path = Path(dir_path)
    if path.exists():
        st.success(f"✓ `{dir_path}` directory exists")
    else:
        st.error(f"✗ `{dir_path}` directory missing!")

# Check for __init__.py files
st.write("### Package Structure Check")
for dir_path in dirs_to_check:
    init_file = Path(dir_path) / "__init__.py"
    if init_file.exists():
        st.success(f"✓ `{dir_path}/__init__.py` exists")
    else:
        st.error(f"✗ `{dir_path}/__init__.py` missing!")

# Critical Files Check
st.write("### Critical Files Check")
critical_files = [
    "app/config/config.py",
    "app/utils/session.py",
    "app/frontend/login_page.py"
]
for file_path in critical_files:
    path = Path(file_path)
    if path.exists():
        st.success(f"✓ `{file_path}` exists")
    else:
        st.error(f"✗ `{file_path}` missing!")

# Import Module Check
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
        st.success(f"✓ Successfully imported `{module}`")
    except Exception as e:
        st.error(f"✗ Failed to import `{module}`: {e}")
        with st.expander("Traceback"):
            st.code(traceback.format_exc())

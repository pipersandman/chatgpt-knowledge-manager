import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys & External Services
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")  # No default localhost fallback
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME")

print(f"Using MongoDB URI: {MONGODB_URI}")  # Debugging

# Application settings
APP_NAME = "AI Knowledge Manager"
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-for-development")

# OpenAI Model Configuration
EMBEDDING_MODEL = "text-embedding-ada-002"  # OpenAI embedding model
GPT_MODEL = "gpt-4-turbo-preview"  # OpenAI chat model

# Define default directories
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(ROOT_DIR, "data")
EXPORT_DIR = os.path.join(ROOT_DIR, "exports")

# Create directories if they don't exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)

# Default categorization settings
DEFAULT_CATEGORIES = [
    "AI & Technology",
    "Writing & Creativity",
    "Business & Strategy",
    "Personal Development",
    "Research & Academia",
    "Uncategorized"
]

# Default tags
DEFAULT_TAGS = [
    "important",
    "follow-up",
    "reference",
    "question",
    "insight"
]
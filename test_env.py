# save as test_env.py
import os
from dotenv import load_dotenv

load_dotenv()
print("OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))
print("MONGODB_URI:", os.getenv("MONGODB_URI"))
print("MONGODB_DB_NAME:", os.getenv("MONGODB_DB_NAME"))
print("SECRET_KEY:", os.getenv("SECRET_KEY"))
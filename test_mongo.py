from pymongo import MongoClient

# Replace with your actual connection string
mongo_uri = "mongodb+srv://tfoster:JywSUqQG826_3@knowledgemanagerdb.gho68.mongodb.net/?retryWrites=true&w=majority&appName=KnowledgeManagerDB"

try:
    # Connect to MongoDB
    client = MongoClient(mongo_uri)
    client.admin.command('ping')  # Test connection
    print("✅ MongoDB Connection Successful!")
except Exception as e:
    print("❌ MongoDB Connection Failed:", e)

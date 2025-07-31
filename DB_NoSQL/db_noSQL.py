import os
import dotenv
import time
from pymongo import MongoClient
from bson import ObjectId

dotenv.load_dotenv()  # Load environment variables from .env file

# Get MongoDB URI from environment variable or use default
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

# Initialize client and database with retry logic
def get_mongo_client():
    """Get MongoDB client with retry logic"""
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            client.admin.command("ping")  # Trigger immediate connection
            return client
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"MongoDB connection attempt {attempt + 1} failed: {e}")
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                print(f"Failed to connect to MongoDB after {max_retries} attempts")
                raise RuntimeError(f"Could not connect to MongoDB: {e}")

# Initialize client and database
try:
    client = get_mongo_client()
    db = client["uws_nosql"]
    print("Successfully connected to MongoDB")
except Exception as e:
    print(f"MongoDB connection error: {e}")
    # Don't raise here, let the functions handle it
    client = None
    db = None

# Dynamic collection functions
def insert_entity(collection_name, entity_data):
    """Insert a document into the specified collection."""
    if not db:
        raise RuntimeError("MongoDB not connected")
    collection = db[collection_name]
    result = collection.insert_one(entity_data)
    return str(result.inserted_id)


def get_entity_by_id(collection_name, entity_id):
    """Get a document by its _id from the specified collection."""
    if not db:
        raise RuntimeError("MongoDB not connected")
    collection = db[collection_name]
    return collection.find_one({"_id": ObjectId(entity_id)})


def list_entities(collection_name):
    """List all documents in the specified collection."""
    if not db:
        raise RuntimeError("MongoDB not connected")
    collection = db[collection_name]
    return list(collection.find())


def delete_entity_by_id(collection_name, entity_id):
    """Delete a document by its _id from the specified collection."""
    if not db:
        raise RuntimeError("MongoDB not connected")
    collection = db[collection_name]
    result = collection.delete_one({"_id": ObjectId(entity_id)})
    return result.deleted_count

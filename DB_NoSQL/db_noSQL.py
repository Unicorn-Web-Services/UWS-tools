import os
import dotenv
from pymongo import MongoClient
from bson import ObjectId

dotenv.load_dotenv()  # Load environment variables from .env file

# Get MongoDB URI from environment variable or use default
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")  # Trigger immediate connection
    db = client["uws_nosql"]
except Exception as e:
    raise RuntimeError(f"Could not connect to MongoDB: {e}")


# Dynamic collection functions
def insert_entity(collection_name, entity_data):
    """Insert a document into the specified collection."""
    collection = db[collection_name]
    result = collection.insert_one(entity_data)
    return str(result.inserted_id)


def get_entity_by_id(collection_name, entity_id):
    """Get a document by its _id from the specified collection."""
    collection = db[collection_name]
    return collection.find_one({"_id": ObjectId(entity_id)})


def list_entities(collection_name):
    """List all documents in the specified collection."""
    collection = db[collection_name]
    return list(collection.find())


def delete_entity_by_id(collection_name, entity_id):
    """Delete a document by its _id from the specified collection."""
    collection = db[collection_name]
    result = collection.delete_one({"_id": ObjectId(entity_id)})
    return result.deleted_count

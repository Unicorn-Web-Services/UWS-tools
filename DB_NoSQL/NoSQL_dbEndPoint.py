from fastapi import APIRouter, HTTPException, File, UploadFile
from pymongo import MongoClient
from pymongo.errors import CollectionInvalid
import os
import base64
from DB_NoSQL.db_noSQL import insert_entity, get_entity_by_id, list_entities, delete_entity_by_id
from bson import ObjectId

router = APIRouter()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client["uws_nosql"]

@router.post("/nosql/create_collection/{collection_name}")
def create_collection(collection_name: str):
    try:
        mongo_db.create_collection(collection_name)
        return {"detail": f"Collection '{collection_name}' created."}
    except CollectionInvalid:
        raise HTTPException(status_code=400, detail="Collection already exists.")

@router.post("/nosql/{collection_name}/save")
async def save_entity(collection_name: str, file: UploadFile = File(None), entity: dict = None):
    if file is not None:
        file_bytes = await file.read()
        encoded_file = base64.b64encode(file_bytes).decode("utf-8")
        if entity is None:
            entity = {}
        entity["filename"] = file.filename
        entity["content_type"] = file.content_type
        entity["file_data_base64"] = encoded_file
    elif entity is None:
        raise HTTPException(status_code=400, detail="No file or entity data provided.")
    inserted_id = insert_entity(collection_name, entity)
    return {"inserted_id": inserted_id}

@router.put("/nosql/{collection_name}/update/{entity_id}")
def update_entity(collection_name: str, entity_id: str, update: dict):
    collection = mongo_db[collection_name]
    result = collection.update_one({"_id": ObjectId(entity_id)}, {"$set": update})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Entity not found.")
    return {"updated_count": result.modified_count}

@router.get("/nosql/{collection_name}/query")
def indexed_query(collection_name: str, field: str, value: str):
    collection = mongo_db[collection_name]
    result = list(collection.find({field: value}))
    for doc in result:
        doc["_id"] = str(doc["_id"])
    return result

@router.get("/nosql/{collection_name}/scan")
def complete_scan(collection_name: str):
    docs = list_entities(collection_name)
    for doc in docs:
        doc["_id"] = str(doc["_id"])
    return docs

@router.get("/nosql/{collection_name}/get/{entity_id}")
def get_entity(collection_name: str, entity_id: str):
    doc = get_entity_by_id(collection_name, entity_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Entity not found.")
    doc["_id"] = str(doc["_id"])
    return doc

@router.delete("/nosql/{collection_name}/delete/{entity_id}")
def delete_entity(collection_name: str, entity_id: str):
    deleted_count = delete_entity_by_id(collection_name, entity_id)
    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="Entity not found.")
    return {"detail": "Entity deleted successfully."}

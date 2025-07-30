
from fastapi import FastAPI, File, UploadFile, Depends
from fastapi.responses import JSONResponse, FileResponse
from fastapi import Header, HTTPException
import uvicorn
import os
from fastapi import Request
# DB imports
from DB.db import SessionLocal, File as DBFile
from fastapi import Form



from pymongo import MongoClient
from pymongo.errors import CollectionInvalid
import dotenv
from DB_NoSQL.db_noSQL import insert_entity, get_entity_by_id, list_entities, delete_entity_by_id
from bson import ObjectId

app = FastAPI()
dotenv.load_dotenv()

@app.get("/")
async def read_root():
    return JSONResponse({"message": "Welcome to UWS-buckets FastAPI server!"})



@app.post("/upload")
async def upload_file(
    user_id: str = Form(...),
    bucket: str = Form(...),
    file: UploadFile = File(...),
    x_signature: str = Header(...)
):
    print("DEBUG HEADERS:", Request.headers)
    print("DEBUG FORM:", user_id, bucket, file.filename, x_signature)
    VALID_SIGNATURE = "mysecretkey123"
    if x_signature != VALID_SIGNATURE:
        raise HTTPException(status_code=401, detail="Invalid signature key")
    # Save file to uploads directory
    uploads_dir = "uploads"
    os.makedirs(uploads_dir, exist_ok=True)
    file_location = os.path.join(uploads_dir, file.filename)
    with open(file_location, "wb") as f:
        content = await file.read()
        f.write(content)

    # Save file metadata to database
    db = SessionLocal()
    db_file = DBFile(
        path=file_location,
        filename=file.filename,
        bucket=bucket,
        user_id=user_id
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    db.close()

    return {
        "filename": file.filename,
        "user_id": user_id,
        "bucket": bucket,
        "detail": "File uploaded successfully.",
        "path": file_location,
        "db_id": db_file.id
    }


# List files endpoint
@app.get("/files")
def list_files():
    db = SessionLocal()
    files = db.query(DBFile).all()
    db.close()
    return [
        {
            "id": f.id,
            "filename": f.filename,
            "bucket": f.bucket,
            "user_id": f.user_id,
            "path": f.path
        }
        for f in files
    ]

# Download file endpoint
@app.get("/download/{file_id}")
def download_file(file_id: int):
    db = SessionLocal()
    db_file = db.query(DBFile).filter(DBFile.id == file_id).first()
    db.close()
    if not db_file or not os.path.exists(db_file.path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(db_file.path, filename=db_file.filename)

# Delete file endpoint
@app.delete("/delete/{file_id}")
def delete_file(file_id: int):
    db = SessionLocal()
    db_file = db.query(DBFile).filter(DBFile.id == file_id).first()
    if not db_file:
        db.close()
        raise HTTPException(status_code=404, detail="File not found")
    # Delete file from disk
    if os.path.exists(db_file.path):
        os.remove(db_file.path)
    # Delete from database
    db.delete(db_file)
    db.commit()
    db.close()
    return {"detail": "File deleted successfully."}


# --- MongoDB (NoSQL) endpoints ---


MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client["uws_nosql"]

# Create collection (table)
@app.post("/nosql/create_collection/{collection_name}")
def create_collection(collection_name: str):
    try:
        mongo_db.create_collection(collection_name)
        return {"detail": f"Collection '{collection_name}' created."}
    except CollectionInvalid:
        raise HTTPException(status_code=400, detail="Collection already exists.")



# Save entity (document) with automatic file encoding
import base64

@app.post("/nosql/{collection_name}/save")
async def save_entity(collection_name: str, file: UploadFile = File(None), entity: dict = None):
    # If a file is uploaded, encode it as base64 and add to entity
    if file is not None:
        file_bytes = await file.read()
        encoded_file = base64.b64encode(file_bytes).decode("utf-8")
        # If entity is not provided, create a new dict
        if entity is None:
            entity = {}
        entity["filename"] = file.filename
        entity["content_type"] = file.content_type
        entity["file_data_base64"] = encoded_file
    elif entity is None:
        raise HTTPException(status_code=400, detail="No file or entity data provided.")
    inserted_id = insert_entity(collection_name, entity)
    return {"inserted_id": inserted_id}


# Update entity
@app.put("/nosql/{collection_name}/update/{entity_id}")
def update_entity(collection_name: str, entity_id: str, update: dict):
    collection = mongo_db[collection_name]
    result = collection.update_one({"_id": ObjectId(entity_id)}, {"$set": update})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Entity not found.")
    return {"updated_count": result.modified_count}



# Indexed query
@app.get("/nosql/{collection_name}/query")
def indexed_query(collection_name: str, field: str, value: str):
    collection = mongo_db[collection_name]
    result = list(collection.find({field: value}))
    for doc in result:
        doc["_id"] = str(doc["_id"])
    return result


# Complete scan
@app.get("/nosql/{collection_name}/scan")
def complete_scan(collection_name: str):
    docs = list_entities(collection_name)
    for doc in docs:
        doc["_id"] = str(doc["_id"])
    return docs


# Get entity by ID
@app.get("/nosql/{collection_name}/get/{entity_id}")
def get_entity(collection_name: str, entity_id: str):
    doc = get_entity_by_id(collection_name, entity_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Entity not found.")
    doc["_id"] = str(doc["_id"])
    return doc


# Delete entity by ID
@app.delete("/nosql/{collection_name}/delete/{entity_id}")
def delete_entity(collection_name: str, entity_id: str):
    deleted_count = delete_entity_by_id(collection_name, entity_id)
    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="Entity not found.")
    return {"detail": "Entity deleted successfully."}

if __name__ == "__main__":
    uvicorn.run("buckets:app", host="127.0.0.1", port=8000, reload=True)

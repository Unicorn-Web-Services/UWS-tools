
from fastapi import FastAPI, File, UploadFile, Depends
from fastapi.responses import JSONResponse, FileResponse
from fastapi import Header, HTTPException
import uvicorn
import os
from fastapi import Request
# DB imports
from DB.db import SessionLocal, File as DBFile
from fastapi import Form


app = FastAPI()


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



if __name__ == "__main__":
    uvicorn.run("buckets:app", host="127.0.0.1", port=8000, reload=True)

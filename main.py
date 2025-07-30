
from fastapi import FastAPI, File, UploadFile, Depends
from fastapi.responses import JSONResponse
from fastapi import Header, HTTPException
import uvicorn
import os
from fastapi import Request


UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


app = FastAPI()


@app.get("/")
async def read_root():
    return JSONResponse({"message": "Welcome to UWS-buckets FastAPI server!"})


from fastapi import Form

@app.post("/upload")
async def upload_file(
    user_id: str = Form(...),
    bucket: str = Form(...),
    file: UploadFile = File(...),
    x_signature: str = Header(...)
):
    print("DEBUG HEADERS:", Request.headers)
    print("DEBUG FORM:", user_id, bucket, file.filename, x_signature)
    # Simple signature key check (replace with secure validation in production)
    VALID_SIGNATURE = "mysecretkey123"
    if x_signature != VALID_SIGNATURE:
        raise HTTPException(status_code=401, detail="Invalid signature key")
    # Create user/bucket directory
    bucket_dir = os.path.join(UPLOAD_DIR, user_id, bucket)
    os.makedirs(bucket_dir, exist_ok=True)
    file_location = os.path.join(bucket_dir, file.filename)
    with open(file_location, "wb") as f:
        content = await file.read()
        f.write(content)
    return {
        "filename": file.filename,
        "user_id": user_id,
        "bucket": bucket,
        "detail": "File uploaded successfully.",
        "path": file_location
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)


from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
import os


DATA_DIR = os.path.join(os.getcwd(), "Data")
os.makedirs(DATA_DIR, exist_ok=True)

# S3-like endpoints router
router = APIRouter()

@router.post("/data/upload")
async def upload_to_data(file: UploadFile = File(...)):
    file_path = os.path.join(DATA_DIR, file.filename)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    return {"filename": file.filename, "detail": "File uploaded to Data folder.", "path": file_path}

@router.get("/data/files")
def list_data_files():
    files = [f for f in os.listdir(DATA_DIR) if os.path.isfile(os.path.join(DATA_DIR, f))]
    return {"files": files}

@router.get("/data/download/{filename}")
def download_data_file(filename: str):
    file_path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found in Data folder.")
    return FileResponse(file_path, filename=filename)

@router.delete("/data/delete/{filename}")
def delete_data_file(filename: str):
    file_path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found in Data folder.")
    os.remove(file_path)
    return {"detail": f"File '{filename}' deleted from Data folder."}



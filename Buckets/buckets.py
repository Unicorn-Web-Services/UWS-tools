
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
import os
from datetime import datetime


DATA_DIR = os.path.join(os.getcwd(), "Data")
os.makedirs(DATA_DIR, exist_ok=True)

# FastAPI app instance
app = FastAPI()

@app.post("/data/upload")
async def upload_to_data(file: UploadFile = File(...)):
    file_path = os.path.join(DATA_DIR, file.filename)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    return {"filename": file.filename, "detail": "File uploaded to Data folder.", "path": file_path}

@app.get("/data/files")
def list_data_files():
    files = [f for f in os.listdir(DATA_DIR) if os.path.isfile(os.path.join(DATA_DIR, f))]
    return {"files": files}

@app.get("/data/download/{filename}")
def download_data_file(filename: str):
    file_path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found in Data folder.")
    return FileResponse(file_path, filename=filename)

@app.delete("/data/delete/{filename}")
def delete_data_file(filename: str):
    file_path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found in Data folder.")
    os.remove(file_path)
    return {"detail": f"File '{filename}' deleted from Data folder."}

@app.get("/health")
def health_check():
    """Health check endpoint for service monitoring"""
    try:
        # Check if DATA_DIR is accessible
        data_dir_exists = os.path.exists(DATA_DIR)
        data_dir_writable = os.access(DATA_DIR, os.W_OK)
        
        # Count files in data directory
        file_count = len([f for f in os.listdir(DATA_DIR) if os.path.isfile(os.path.join(DATA_DIR, f))])
        
        return {
            "status": "healthy",
            "service": "bucket-service",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "data_directory_exists": data_dir_exists,
                "data_directory_writable": data_dir_writable,
                "file_count": file_count
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")



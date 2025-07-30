from fastapi import APIRouter, File, UploadFile, Depends, Header, HTTPException, Form
from fastapi.responses import JSONResponse, FileResponse
from DB.db import SessionLocal, File as DBFile
import os
# Resource limiting imports
import psutil
import shutil

router = APIRouter()

@router.post("/upload")
async def upload_file(
    user_id: str = Form(...),
    bucket: str = Form(...),
    file: UploadFile = File(...),
    x_signature: str = Header(...)
):
    VALID_SIGNATURE = "mysecretkey123"
    if x_signature != VALID_SIGNATURE:
        raise HTTPException(status_code=401, detail="Invalid signature key")

    # Resource limits (customize as needed)
    MAX_CPU_PERCENT = 90  # percent
    MAX_RAM_MB = 2048     # MB
    MAX_DISK_GB = 10      # GB, free space required

    # Check CPU usage
    cpu_percent = psutil.cpu_percent(interval=1)
    if cpu_percent > MAX_CPU_PERCENT:
        raise HTTPException(status_code=503, detail=f"Server overloaded: CPU usage {cpu_percent}% exceeds limit {MAX_CPU_PERCENT}%")

    # Check RAM usage (current process only)
    process = psutil.Process(os.getpid())
    used_ram_mb = process.memory_info().rss / (1024 * 1024)
    if used_ram_mb > MAX_RAM_MB:
        raise HTTPException(status_code=503, detail=f"Server overloaded: App RAM usage {used_ram_mb:.2f}MB exceeds limit {MAX_RAM_MB}MB")

    # Check disk space
    disk = shutil.disk_usage(os.getcwd())
    free_disk_gb = disk.free / (1024 * 1024 * 1024)
    if free_disk_gb < MAX_DISK_GB:
        raise HTTPException(status_code=507, detail=f"Insufficient disk space: {free_disk_gb:.2f}GB free, require at least {MAX_DISK_GB}GB")

    file_location = file.filename
    with open(file_location, "wb") as f:
        content = await file.read()
        f.write(content)
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

@router.get("/files")
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

@router.get("/download/{file_id}")
def download_file(file_id: int):
    db = SessionLocal()
    db_file = db.query(DBFile).filter(DBFile.id == file_id).first()
    db.close()
    if not db_file or not os.path.exists(db_file.path):
        raise HTTPException(status_code=404, detail="File not found")
    # Pass file path directly to FileResponse for proper binary streaming
    return FileResponse(db_file.path, filename=db_file.filename)

@router.delete("/delete/{file_id}")
def delete_file(file_id: int):
    db = SessionLocal()
    db_file = db.query(DBFile).filter(DBFile.id == file_id).first()
    if not db_file:
        db.close()
        raise HTTPException(status_code=404, detail="File not found")
    if os.path.exists(db_file.path):
        os.remove(db_file.path)
    db.delete(db_file)
    db.commit()
    db.close()
    return {"detail": "File deleted successfully."}

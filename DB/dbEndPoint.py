from fastapi import FastAPI, File, UploadFile, Header, HTTPException, Form
from fastapi.responses import FileResponse
from DB.db import insert_entity, get_entity_by_id, list_entities, delete_entity_by_id
import os

# Resource limiting imports
import psutil
import shutil

app = FastAPI()


@app.post("/upload/{table_name}")
async def upload_file(
    table_name: str,
    user_id: str = Form(...),
    bucket: str = Form(...),
    file: UploadFile = File(...),
    x_signature: str = Header(...),
):
    VALID_SIGNATURE = "mysecretkey123"
    if x_signature != VALID_SIGNATURE:
        raise HTTPException(status_code=401, detail="Invalid signature key")

    # Resource limits (customize as needed)
    MAX_CPU_PERCENT = 90  # percent
    MAX_RAM_MB = 2048  # MB
    MAX_DISK_GB = 10  # GB, free space required

    # Check CPU usage
    cpu_percent = psutil.cpu_percent(interval=1)
    if cpu_percent > MAX_CPU_PERCENT:
        raise HTTPException(
            status_code=503,
            detail=f"Server overloaded: CPU usage {cpu_percent}% exceeds limit {MAX_CPU_PERCENT}%",
        )

    # Check RAM usage (current process only)
    process = psutil.Process(os.getpid())
    used_ram_mb = process.memory_info().rss / (1024 * 1024)
    if used_ram_mb > MAX_RAM_MB:
        raise HTTPException(
            status_code=503,
            detail=f"Server overloaded: App RAM usage {used_ram_mb:.2f}MB exceeds limit {MAX_RAM_MB}MB",
        )

    # Check disk space
    disk = shutil.disk_usage(os.getcwd())
    free_disk_gb = disk.free / (1024 * 1024 * 1024)
    if free_disk_gb < MAX_DISK_GB:
        raise HTTPException(
            status_code=507,
            detail=f"Insufficient disk space: {free_disk_gb:.2f}GB free, require at least {MAX_DISK_GB}GB",
        )

    file_location = file.filename
    with open(file_location, "wb") as f:
        content = await file.read()
        f.write(content)
    entity = {
        "path": file_location,
        "filename": file.filename,
        "bucket": bucket,
        "user_id": user_id,
    }
    db_id = insert_entity(table_name, entity)
    return {
        "filename": file.filename,
        "user_id": user_id,
        "bucket": bucket,
        "detail": "File uploaded successfully.",
        "path": file_location,
        "db_id": db_id,
    }


@app.get("/files/{table_name}")
def list_files(table_name: str):
    files = list_entities(table_name)
    return files


@app.get("/download/{table_name}/{entity_id}")
def download_file(table_name: str, entity_id: int):
    db_file = get_entity_by_id(table_name, entity_id)
    if not db_file or not os.path.exists(db_file["path"]):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(db_file["path"], filename=db_file["filename"])


@app.delete("/delete/{table_name}/{entity_id}")
def delete_file(table_name: str, entity_id: int):
    db_file = get_entity_by_id(table_name, entity_id)
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
    if os.path.exists(db_file["path"]):
        os.remove(db_file["path"])
    deleted_count = delete_entity_by_id(table_name, entity_id)
    return {
        "detail": "File deleted successfully." if deleted_count else "File not deleted."
    }

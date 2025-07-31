from fastapi import FastAPI, File, UploadFile, Header, HTTPException, Form, Body
from fastapi.responses import FileResponse
from db import insert_entity, get_entity_by_id, list_entities, delete_entity_by_id, execute_sql_query, get_database_stats
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from sqlalchemy import text

# Resource limiting imports
import psutil
import shutil

app = FastAPI()

# Resource limits configuration - can be overridden via environment variables
DEFAULT_RESOURCE_LIMITS = {
    "max_cpu_percent": int(os.getenv("MAX_CPU_PERCENT", "90")),
    "max_ram_mb": int(os.getenv("MAX_RAM_MB", "2048")),
    "max_disk_gb": int(os.getenv("MAX_DISK_GB", "10"))
}

class SQLQueryRequest(BaseModel):
    query: str
    params: Optional[Dict[str, Any]] = None

class ResourceLimitsRequest(BaseModel):
    max_cpu_percent: Optional[int] = None
    max_ram_mb: Optional[int] = None 
    max_disk_gb: Optional[int] = None

class DatabaseInstanceConfig(BaseModel):
    name: Optional[str] = None
    resource_limits: Optional[ResourceLimitsRequest] = None


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

    # Check resource limits
    check_resource_limits()

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

def check_resource_limits():
    """Check if current resource usage is within limits"""
    limits = DEFAULT_RESOURCE_LIMITS
    
    # Check CPU usage
    cpu_percent = psutil.cpu_percent(interval=0.5)
    if cpu_percent > limits["max_cpu_percent"]:
        raise HTTPException(
            status_code=503,
            detail=f"Server overloaded: CPU usage {cpu_percent}% exceeds limit {limits['max_cpu_percent']}%",
        )

    # Check RAM usage (current process only)
    process = psutil.Process(os.getpid())
    used_ram_mb = process.memory_info().rss / (1024 * 1024)
    if used_ram_mb > limits["max_ram_mb"]:
        raise HTTPException(
            status_code=503,
            detail=f"Server overloaded: App RAM usage {used_ram_mb:.2f}MB exceeds limit {limits['max_ram_mb']}MB",
        )

    # Check disk space
    disk = shutil.disk_usage(os.getcwd())
    free_disk_gb = disk.free / (1024 * 1024 * 1024)
    if free_disk_gb < limits["max_disk_gb"]:
        raise HTTPException(
            status_code=507,
            detail=f"Insufficient disk space: {free_disk_gb:.2f}GB free, require at least {limits['max_disk_gb']}GB",
        )


@app.post("/sql/query")
def execute_sql(query_request: SQLQueryRequest, x_signature: str = Header(...)):
    """Execute SQL queries against the database"""
    VALID_SIGNATURE = "mysecretkey123"
    if x_signature != VALID_SIGNATURE:
        raise HTTPException(status_code=401, detail="Invalid signature key")
    
    # Check resource limits before executing query
    check_resource_limits()
    
    try:
        result = execute_sql_query(query_request.query, query_request.params)
        return {
            "success": True,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"SQL execution failed: {str(e)}")


@app.get("/sql/tables")
def list_tables(x_signature: str = Header(...)):
    """List all available tables in the database"""
    VALID_SIGNATURE = "mysecretkey123"
    if x_signature != VALID_SIGNATURE:
        raise HTTPException(status_code=401, detail="Invalid signature key")
    
    try:
        tables = execute_sql_query("SELECT name FROM sqlite_master WHERE type='table'")
        return {
            "tables": [table[0] for table in tables],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tables: {str(e)}")


@app.get("/sql/schema/{table_name}")
def get_table_schema(table_name: str, x_signature: str = Header(...)):
    """Get schema information for a specific table"""
    VALID_SIGNATURE = "mysecretkey123"
    if x_signature != VALID_SIGNATURE:
        raise HTTPException(status_code=401, detail="Invalid signature key")
    
    try:
        schema = execute_sql_query(f"PRAGMA table_info({table_name})")
        return {
            "table_name": table_name,
            "columns": [
                {
                    "name": row[1],
                    "type": row[2],
                    "not_null": bool(row[3]),
                    "default_value": row[4],
                    "primary_key": bool(row[5])
                }
                for row in schema
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get table schema: {str(e)}")


@app.get("/config/resource-limits")
def get_resource_limits(x_signature: str = Header(...)):
    """Get current resource limits configuration"""
    VALID_SIGNATURE = "mysecretkey123"
    if x_signature != VALID_SIGNATURE:
        raise HTTPException(status_code=401, detail="Invalid signature key")
    
    return {
        "resource_limits": DEFAULT_RESOURCE_LIMITS,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/config/resource-limits")
def update_resource_limits(limits: ResourceLimitsRequest, x_signature: str = Header(...)):
    """Update resource limits configuration"""
    VALID_SIGNATURE = "mysecretkey123"
    if x_signature != VALID_SIGNATURE:
        raise HTTPException(status_code=401, detail="Invalid signature key")
    
    global DEFAULT_RESOURCE_LIMITS
    
    if limits.max_cpu_percent is not None:
        DEFAULT_RESOURCE_LIMITS["max_cpu_percent"] = limits.max_cpu_percent
    if limits.max_ram_mb is not None:
        DEFAULT_RESOURCE_LIMITS["max_ram_mb"] = limits.max_ram_mb
    if limits.max_disk_gb is not None:
        DEFAULT_RESOURCE_LIMITS["max_disk_gb"] = limits.max_disk_gb
    
    return {
        "message": "Resource limits updated successfully",
        "new_limits": DEFAULT_RESOURCE_LIMITS,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/stats")
def get_database_statistics(x_signature: str = Header(...)):
    """Get database usage statistics and metrics"""
    VALID_SIGNATURE = "mysecretkey123"
    if x_signature != VALID_SIGNATURE:
        raise HTTPException(status_code=401, detail="Invalid signature key")
    
    try:
        stats = get_database_stats()
        return {
            "database_stats": stats,
            "resource_usage": {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_free_gb": shutil.disk_usage(os.getcwd()).free / (1024**3)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@app.get("/health")
def health_check():
    """Enhanced health check endpoint for service monitoring"""
    try:
        try:
            from db import engine
        except ImportError:
            from .db import engine
        
        # Test database connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        # Check system resources
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory_info = psutil.virtual_memory()
        disk_usage = shutil.disk_usage(os.getcwd())
        
        # Check if within resource limits
        within_limits = (
            cpu_percent <= DEFAULT_RESOURCE_LIMITS["max_cpu_percent"] and
            memory_info.percent <= 90 and  # General memory check
            disk_usage.free / (1024**3) >= DEFAULT_RESOURCE_LIMITS["max_disk_gb"]
        )
        
        return {
            "status": "healthy" if within_limits else "warning",
            "service": "database-service",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "database_connection": True,
                "cpu_usage_percent": cpu_percent,
                "memory_usage_percent": memory_info.percent,
                "disk_free_gb": disk_usage.free / (1024**3),
                "within_resource_limits": within_limits
            },
            "resource_limits": DEFAULT_RESOURCE_LIMITS
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

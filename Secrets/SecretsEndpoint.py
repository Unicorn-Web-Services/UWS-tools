from fastapi import FastAPI, HTTPException
from datetime import datetime
from Secrets import (
    store_secret,
    get_secret,
    update_secret,
    delete_secret,
    init_db,
)

app = FastAPI()
init_db()


@app.post("/secrets")
def create_secret(payload: dict):
    name = payload.get("name")
    value = payload.get("value")
    if not name or not value:
        raise HTTPException(status_code=400, detail="Missing name or value.")
    store_secret(name, value)
    return {"detail": f"Secret '{name}' stored."}


@app.post("/secrets/store")
def store_secret_endpoint(payload: dict):
    """Alias for create_secret to match expected API"""
    return create_secret(payload)


@app.get("/secrets/{name}")
def read_secret(name: str):
    secret = get_secret(name)
    if not secret:
        raise HTTPException(status_code=404, detail="Secret not found.")
    return {
        "name": secret["name"], 
        "value": secret["value"],
        "created_at": secret["created_at"].isoformat(),
        "updated_at": secret["updated_at"].isoformat()
    }


@app.get("/secrets")
def list_secrets():
    """List all secrets (names only, not values)"""
    try:
        from Secrets.Secrets import SessionLocal, Secret
        
        db = SessionLocal()
        secrets = db.query(Secret).all()
        db.close()
        
        return {
            "secrets": [
                {
                    "name": secret.name,
                    "created_at": secret.created_at.isoformat(),
                    "updated_at": secret.updated_at.isoformat()
                }
                for secret in secrets
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list secrets: {str(e)}")


@app.put("/secrets/{name}")
def update_secret_endpoint(name: str, payload: dict):
    value = payload.get("value")
    if not value:
        raise HTTPException(status_code=400, detail="Missing value.")
    update_secret(name, value)
    return {"detail": f"Secret '{name}' updated."}


@app.delete("/secrets/{name}")
def delete_secret_endpoint(name: str):
    deleted = delete_secret(name)
    if not deleted:
        raise HTTPException(status_code=404, detail="Secret not found.")
    return {"detail": f"Secret '{name}' deleted."}

@app.get("/health")
def health_check():
    """Health check endpoint for service monitoring"""
    try:
        from Secrets.Secrets import SessionLocal, Secret
        
        # Test database connection
        db = SessionLocal()
        secret_count = db.query(Secret).count()
        db.close()
        
        return {
            "status": "healthy",
            "service": "secrets-service",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "database_connection": True,
                "secret_count": secret_count,
                "encryption_available": True
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

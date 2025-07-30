from fastapi import FastAPI

from DB.dbEndPoint import app as db_app
from DB_NoSQL.NoSQL_dbEndPoint import app as nosql_app
from Queue.QueueEndpoints import app as queue_app
from Buckets.buckets import app as s3_app
from Secrets.SecretsEndpoint import app as secrets_app

# Main FastAPI application
app = FastAPI(title="UWS Tools API", description="Unified Web Services Tools API")

# Mount sub-applications
app.mount("/db", db_app)
app.mount("/nosql", nosql_app)
app.mount("/queue", queue_app)
app.mount("/buckets", s3_app)
app.mount("/secrets", secrets_app)


@app.get("/")
async def read_root():
    return {"message": "Welcome to UWS FastAPI server!"}


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "services": ["db", "nosql", "queue", "buckets", "secrets"],
    }

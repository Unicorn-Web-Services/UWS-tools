from fastapi import APIRouter
from DB.dbEndPoint import router as db_router
from DB_NoSQL.NoSQL_dbEndPoint import router as nosql_router
from Queue.QueueEndpoints import router as queue_router
from Buckets.buckets import router as s3_router  

from fastapi import FastAPI

router = APIRouter()
router.include_router(db_router)
router.include_router(nosql_router)
router.include_router(queue_router)
router.include_router(s3_router)

app = FastAPI()
app.include_router(router)

@app.get("/")
async def read_root():
    return {"message": "Welcome to UWS FastAPI server!"}

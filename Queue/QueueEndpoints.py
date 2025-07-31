from fastapi import FastAPI, HTTPException, Body
from datetime import datetime
from Queue import add_message, read_messages, delete_message_by_id

app = FastAPI()


# Add message to queue
@app.post("/queue/add")
def queue_add(message: dict = Body(...)):
    if "message" not in message:
        raise HTTPException(status_code=400, detail="Missing 'message' field.")
    msg = add_message(message["message"])
    return {
        "id": msg["id"],
        "message": msg["message"],
        "timestamp": datetime.utcnow().isoformat()
    }


# Read messages from queue
@app.get("/queue/read")
def queue_read(limit: int = 10):
    msgs = read_messages(limit)
    return [
        {
            "id": msg["id"],
            "message": msg["message"],
            "timestamp": datetime.utcnow().isoformat()
        }
        for msg in msgs
    ]


# Delete message by ID
@app.delete("/queue/{message_id}")
def queue_delete(message_id: str):
    deleted = delete_message_by_id(message_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Message not found.")
    return {"deleted": True, "message_id": message_id}

@app.get("/health")
def health_check():
    """Health check endpoint for service monitoring"""
    try:
        # Get current queue status
        messages = read_messages(limit=1000)  # Get all messages to count
        message_count = len(messages)
        
        return {
            "status": "healthy",
            "service": "queue-service",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "queue_accessible": True,
                "message_count": message_count,
                "queue_type": "in-memory"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

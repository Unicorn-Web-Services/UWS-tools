from fastapi import FastAPI, HTTPException, Body
from Queue.Queue import add_message, read_messages, delete_message_by_id

app = FastAPI()


# Add message to queue
@app.post("/queue")
def queue_add(message: dict = Body(...)):
    if "message" not in message:
        raise HTTPException(status_code=400, detail="Missing 'message' field.")
    msg = add_message(message["message"])
    return msg


# Read messages from queue
@app.get("/queue")
def queue_read(limit: int = 10):
    msgs = read_messages(limit)
    return msgs


# Delete message by ID
@app.delete("/queue/{message_id}")
def queue_delete(message_id: str):
    deleted = delete_message_by_id(message_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Message not found.")
    return {"detail": "Message deleted."}

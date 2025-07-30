import uuid
import threading
from collections import deque

# Simple in-memory queue (thread-safe)
_queue_lock = threading.Lock()
_queue = deque()

def add_message(message_text):
    """Add a message to the queue. Returns the message dict with id."""
    message_id = str(uuid.uuid4())
    message = {"id": message_id, "message": message_text}
    with _queue_lock:
        _queue.append(message)
    return message

def read_messages(limit=10):
    """Read up to 'limit' messages from the queue (peek, do not remove)."""
    with _queue_lock:
        return list(_queue)[:limit]

def delete_message_by_id(message_id):
    """Delete a message from the queue by its id. Returns True if deleted."""
    with _queue_lock:
        for i, msg in enumerate(_queue):
            if msg["id"] == message_id:
                del _queue[i]
                return True
    return False

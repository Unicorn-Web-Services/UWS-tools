from fastapi import FastAPI, HTTPException
from Secrets.Secrets import (
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


@app.get("/secrets/{name}")
def read_secret(name: str):
    secret = get_secret(name)
    if not secret:
        raise HTTPException(status_code=404, detail="Secret not found.")
    return {"name": secret["name"], "value": secret["value"]}


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

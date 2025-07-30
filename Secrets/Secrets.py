
import os
import base64
from datetime import datetime
from cryptography.fernet import Fernet
from sqlalchemy import create_engine, Column, String, LargeBinary, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Master key (in real AWS, use KMS; here, local file or env)
FERNET_KEY = os.getenv("SECRETS_FERNET_KEY")
if not FERNET_KEY:
    # Generate and save a key if not present
    FERNET_KEY = Fernet.generate_key()
    # For demo, save to file
    with open("secrets_master.key", "wb") as f:
        f.write(FERNET_KEY)
FERNET = Fernet(FERNET_KEY)

# SQLite DB for demo
DATABASE_URL = os.getenv("SECRETS_DB_URL", "sqlite:///./secrets.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Secret(Base):
    __tablename__ = "secrets"
    name = Column(String, primary_key=True, index=True)
    encrypted_value = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def encrypt_secret(value: str) -> bytes:
    return FERNET.encrypt(value.encode())

def decrypt_secret(encrypted_value: bytes) -> str:
    return FERNET.decrypt(encrypted_value).decode()

def store_secret(name: str, value: str):
    db = SessionLocal()
    encrypted = encrypt_secret(value)
    now = datetime.utcnow()
    secret = db.query(Secret).filter(Secret.name == name).first()
    if secret:
        secret.encrypted_value = encrypted
        secret.updated_at = now
    else:
        secret = Secret(name=name, encrypted_value=encrypted, created_at=now, updated_at=now)
        db.add(secret)
    db.commit()
    db.close()

def get_secret(name: str):
    db = SessionLocal()
    secret = db.query(Secret).filter(Secret.name == name).first()
    db.close()
    if not secret:
        return None
    return {
        "name": secret.name,
        "value": decrypt_secret(secret.encrypted_value),
        "created_at": secret.created_at,
        "updated_at": secret.updated_at
    }

def update_secret(name: str, value: str):
    return store_secret(name, value)

def delete_secret(name: str):
    db = SessionLocal()
    secret = db.query(Secret).filter(Secret.name == name).first()
    if not secret:
        db.close()
        return False
    db.delete(secret)
    db.commit()
    db.close()
    return True

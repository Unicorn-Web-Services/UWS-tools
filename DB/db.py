
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import dotenv

dotenv.load_dotenv()  # Load environment variables from .env file

# Get DATABASE_URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable not set")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class File(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True, index=True)
    path = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    bucket = Column(String, nullable=False)
    user_id = Column(String, nullable=False)

def init_db():
    Base.metadata.create_all(bind=engine)

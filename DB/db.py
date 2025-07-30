from sqlalchemy import create_engine, MetaData, Table
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
metadata = MetaData()

def get_table(table_name):
    """Reflect and return a Table object for the given table name."""
    metadata.reflect(bind=engine)
    if table_name not in metadata.tables:
        raise RuntimeError(f"Table '{table_name}' does not exist.")
    return metadata.tables[table_name]

def insert_entity(table_name, entity_data):
    """Insert a row into the specified table."""
    table = get_table(table_name)
    with engine.begin() as conn:
        result = conn.execute(table.insert().values(**entity_data))
        return result.inserted_primary_key[0] if result.inserted_primary_key else None

def get_entity_by_id(table_name, entity_id):
    """Get a row by its primary key from the specified table."""
    table = get_table(table_name)
    pk_col = list(table.primary_key.columns)[0]
    with engine.connect() as conn:
        result = conn.execute(table.select().where(pk_col == entity_id)).fetchone()
        return dict(result._mapping) if result else None

def list_entities(table_name):
    """List all rows in the specified table."""
    table = get_table(table_name)
    with engine.connect() as conn:
        result = conn.execute(table.select()).fetchall()
        return [dict(row._mapping) for row in result]

def delete_entity_by_id(table_name, entity_id):
    """Delete a row by its primary key from the specified table."""
    table = get_table(table_name)
    pk_col = list(table.primary_key.columns)[0]
    with engine.begin() as conn:
        result = conn.execute(table.delete().where(pk_col == entity_id))
        return result.rowcount

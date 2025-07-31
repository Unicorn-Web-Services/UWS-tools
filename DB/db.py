from sqlalchemy import create_engine, MetaData, Table, text
from sqlalchemy.orm import sessionmaker
import os
import dotenv
from typing import Dict, Any, Optional, List, Tuple

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


def execute_sql_query(query: str, params: Optional[Dict[str, Any]] = None) -> List[Tuple]:
    """Execute a raw SQL query and return results."""
    try:
        with engine.connect() as conn:
            if params:
                result = conn.execute(text(query), params)
            else:
                result = conn.execute(text(query))
            
            # For SELECT queries, fetch results
            if query.strip().upper().startswith('SELECT') or query.strip().upper().startswith('PRAGMA'):
                return result.fetchall()
            else:
                # For INSERT, UPDATE, DELETE queries, commit and return rowcount
                conn.commit()
                return [("Query executed successfully", result.rowcount)]
    except Exception as e:
        raise RuntimeError(f"SQL execution failed: {str(e)}")


def get_database_stats() -> Dict[str, Any]:
    """Get database statistics and usage information."""
    try:
        stats = {}
        
        with engine.connect() as conn:
            # Get database file size (SQLite specific)
            try:
                db_size = conn.execute(text("PRAGMA page_count")).fetchone()[0]
                page_size = conn.execute(text("PRAGMA page_size")).fetchone()[0]
                stats["database_size_bytes"] = db_size * page_size
                stats["database_size_mb"] = (db_size * page_size) / (1024 * 1024)
            except:
                stats["database_size_bytes"] = None
                stats["database_size_mb"] = None
            
            # Get table count
            try:
                table_count = conn.execute(text("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")).fetchone()[0]
                stats["table_count"] = table_count
            except:
                stats["table_count"] = None
            
            # Get table information
            try:
                tables_info = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
                stats["tables"] = [table[0] for table in tables_info]
                
                # Get row counts for each table
                table_stats = {}
                for table_name in stats["tables"]:
                    try:
                        row_count = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).fetchone()[0]
                        table_stats[table_name] = {"row_count": row_count}
                    except:
                        table_stats[table_name] = {"row_count": None}
                
                stats["table_statistics"] = table_stats
            except:
                stats["tables"] = []
                stats["table_statistics"] = {}
        
        return stats
    except Exception as e:
        raise RuntimeError(f"Failed to get database statistics: {str(e)}")


def create_table_from_sql(sql_statement: str) -> bool:
    """Execute a CREATE TABLE statement."""
    try:
        with engine.begin() as conn:
            conn.execute(text(sql_statement))
            return True
    except Exception as e:
        raise RuntimeError(f"Failed to create table: {str(e)}")


def drop_table(table_name: str) -> bool:
    """Drop a table from the database."""
    try:
        with engine.begin() as conn:
            conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
            return True
    except Exception as e:
        raise RuntimeError(f"Failed to drop table: {str(e)}")

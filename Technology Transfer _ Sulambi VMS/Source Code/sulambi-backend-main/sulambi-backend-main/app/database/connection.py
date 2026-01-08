from dotenv import load_dotenv
import sqlite3
import os

load_dotenv()
DB_PATH = os.getenv("DB_PATH")
DATABASE_URL = os.getenv("DATABASE_URL")  # For PostgreSQL (production)

def quote_identifier(identifier):
    """Quote identifier for PostgreSQL (case-sensitive), leave unquoted for SQLite"""
    if DATABASE_URL and DATABASE_URL.startswith('postgresql://'):
        return f'"{identifier}"'
    return identifier

def convert_placeholders(query):
    """Convert SQLite ? placeholders to PostgreSQL %s placeholders if needed"""
    if DATABASE_URL and DATABASE_URL.startswith('postgresql://'):
        return query.replace('?', '%s')
    return query

def is_postgresql_connection(conn):
    """Check if connection is PostgreSQL by checking connection type"""
    try:
        # Check if it's a psycopg2 connection
        return hasattr(conn, 'server_version') or type(conn).__module__.startswith('psycopg2')
    except:
        return False

def convert_boolean_value(value):
    """Convert boolean value for database compatibility
    PostgreSQL uses true/false, SQLite uses 1/0
    """
    if DATABASE_URL and DATABASE_URL.startswith('postgresql://'):
        # PostgreSQL: convert 1/0 to true/false
        if value == 1 or value == True:
            return True
        elif value == 0 or value == False:
            return False
        return value
    else:
        # SQLite: convert true/false to 1/0
        if value == True:
            return 1
        elif value == False:
            return 0
        return value

def convert_boolean_condition(condition):
    """Convert boolean conditions in SQL queries
    PostgreSQL: column = true/false
    SQLite: column = 1/0
    """
    if DATABASE_URL and DATABASE_URL.startswith('postgresql://'):
        # Replace = 1 with = true, = 0 with = false
        condition = condition.replace(' = 1', ' = true')
        condition = condition.replace(' = 0', ' = false')
        condition = condition.replace('= 1', '= true')
        condition = condition.replace('= 0', '= false')
    return condition

def cursorInstance():
  # Use PostgreSQL if DATABASE_URL is provided (production)
  if DATABASE_URL and DATABASE_URL.startswith('postgresql://'):
    try:
      import psycopg2
      from urllib.parse import urlparse
      
      result = urlparse(DATABASE_URL)
      connect = psycopg2.connect(
        database=result.path[1:],  # Remove leading '/'
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port or 5432
      )
      return connect, connect.cursor()
    except ImportError:
      print("Warning: psycopg2 not installed. Install with: pip install psycopg2-binary")
      print("Falling back to SQLite...")
    except Exception as e:
      print(f"Error connecting to PostgreSQL: {e}")
      print("Falling back to SQLite...")
  
  # Fallback to SQLite (local development)
  db_path = DB_PATH or os.getenv("DB_PATH") or "app/database/database.db"
  
  connect = sqlite3.connect(db_path, timeout=30.0)
  connect.execute("PRAGMA journal_mode=WAL")
  connect.execute("PRAGMA synchronous=NORMAL")
  connect.execute("PRAGMA cache_size=1000")
  connect.execute("PRAGMA temp_store=MEMORY")
  return connect, connect.cursor()


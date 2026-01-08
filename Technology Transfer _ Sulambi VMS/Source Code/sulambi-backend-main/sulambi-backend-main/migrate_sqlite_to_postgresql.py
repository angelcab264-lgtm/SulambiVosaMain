#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migrate data from SQLite database to PostgreSQL database
Run this script locally with DATABASE_URL pointing to your Render PostgreSQL database
"""

import sqlite3
import os
import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

# Local SQLite database
DB_PATH = os.getenv("DB_PATH", "app/database/database.db")
if not os.path.isabs(DB_PATH):
    DB_PATH = os.path.join(os.path.dirname(__file__), DB_PATH)

# PostgreSQL connection from DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL environment variable not set!")
    print("Please set DATABASE_URL to your Render PostgreSQL connection string")
    print("\nFrom Render Dashboard:")
    print("1. Go to sulambi-database → Connection Info tab")
    print("2. Copy the 'External Database URL' (for connecting from your local machine)")
    print("3. Internal Database URL is only for services within Render's network")
    print("\nExample: postgresql://user:password@host:port/database")
    sys.exit(1)

print("=" * 70, flush=True)
print("MIGRATING SQLITE DATABASE TO POSTGRESQL", flush=True)
print("=" * 70, flush=True)
print(f"Source (SQLite): {DB_PATH}", flush=True)
print(f"Target (PostgreSQL): {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'Hidden'}", flush=True)

# Parse PostgreSQL URL
try:
    import psycopg2
    result = urlparse(DATABASE_URL)
    
    pg_conn = psycopg2.connect(
        database=result.path[1:],  # Remove leading '/'
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port or 5432
    )
    pg_cursor = pg_conn.cursor()
    print("✓ Connected to PostgreSQL database", flush=True)
except ImportError:
    print("❌ ERROR: psycopg2 not installed. Install with: pip install psycopg2-binary", flush=True)
    sys.exit(1)
except Exception as e:
    print(f"❌ ERROR connecting to PostgreSQL: {e}", flush=True)
    sys.exit(1)

# Connect to SQLite
if not os.path.exists(DB_PATH):
    print(f"❌ ERROR: SQLite database not found at: {DB_PATH}", flush=True)
    sys.exit(1)

sqlite_conn = sqlite3.connect(DB_PATH)
sqlite_cursor = sqlite_conn.cursor()
print("✓ Connected to SQLite database", flush=True)

# Get all tables from SQLite
sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
tables = [row[0] for row in sqlite_cursor.fetchall()]
print(f"\nFound {len(tables)} tables to migrate: {', '.join(tables)}", flush=True)
print(f"Starting migration...\n", flush=True)

# Map SQLite types to PostgreSQL types
type_mapping = {
    'INTEGER': 'INTEGER',
    'TEXT': 'TEXT',
    'REAL': 'REAL',
    'BLOB': 'BYTEA',
    'NUMERIC': 'NUMERIC',
}

def get_columns(cursor, table_name):
    """Get column information from SQLite"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return cursor.fetchall()

def migrate_table(table_name):
    """Migrate a single table from SQLite to PostgreSQL"""
    print(f"\n{'='*70}", flush=True)
    print(f"Migrating table: {table_name}", flush=True)
    print(f"{'='*70}", flush=True)
    
    try:
        # Get table structure
        columns = get_columns(sqlite_cursor, table_name)
        print(f"  Found {len(columns)} columns", flush=True)
        
        # Get all data from SQLite
        sqlite_cursor.execute(f"SELECT * FROM {table_name}")
        rows = sqlite_cursor.fetchall()
        
        if len(rows) == 0:
            print(f"  ⚠️  Table is empty, skipping...", flush=True)
            return
        
        print(f"  Found {len(rows)} rows to migrate", flush=True)
        
        # Get column names
        column_names = [col[1] for col in columns]
        
        # Check if table exists, if not, skip with message
        pg_cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = %s
            );
        """, (table_name.lower(),))
        table_exists = pg_cursor.fetchone()[0]
        
        if not table_exists:
            print(f"  ⚠️  Table '{table_name}' does not exist in PostgreSQL!", flush=True)
            print(f"  ⚠️  Please run 'python server.py --init' on Render first to create tables", flush=True)
            print(f"  ⚠️  Or create tables manually in PostgreSQL", flush=True)
            return
        
        # Note: Data is already cleared before migration starts (see above)
        # This section is kept for reference but data should already be cleared
        
        # Get PostgreSQL column types to handle type conversion
        pg_cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = %s
            ORDER BY ordinal_position
        """, (table_name.lower(),))
        pg_columns = {row[0]: row[1] for row in pg_cursor.fetchall()}
        
        # Insert data - use savepoints for each row to handle errors gracefully
        placeholders = ', '.join(['%s'] * len(column_names))
        column_names_str = ', '.join(column_names)
        
        inserted = 0
        total_rows = len(rows)
        # Show progress every 10% or every 100 rows, whichever is smaller
        progress_interval = max(1, min(100, total_rows // 10))
        
        for i, row in enumerate(rows, 1):
            try:
                # Create a savepoint for this row
                savepoint_name = f"sp_row_{i}"
                pg_cursor.execute(f"SAVEPOINT {savepoint_name}")
                
                # Convert None to NULL, handle BLOB data, and convert INTEGER to BOOLEAN
                values = []
                for idx, (col_name, val) in enumerate(zip(column_names, row)):
                    if val is None:
                        values.append(None)
                    elif isinstance(val, bytes):
                        values.append(val)
                    else:
                        # Convert INTEGER (0/1) to BOOLEAN for boolean columns
                        pg_col_type = pg_columns.get(col_name.lower(), '').upper()
                        if pg_col_type == 'BOOLEAN' and isinstance(val, int):
                            values.append(bool(val))
                        else:
                            values.append(val)
                
                pg_cursor.execute(
                    f"INSERT INTO {table_name} ({column_names_str}) VALUES ({placeholders})",
                    values
                )
                pg_cursor.execute(f"RELEASE SAVEPOINT {savepoint_name}")
                inserted += 1
                
                # Show progress
                if i % progress_interval == 0 or i == total_rows:
                    percentage = (i / total_rows) * 100
                    print(f"  Progress: {i}/{total_rows} rows ({percentage:.1f}%) - {inserted} inserted", flush=True)
                    
            except Exception as e:
                # Rollback to savepoint to continue with next row
                pg_cursor.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
                print(f"  ⚠️  Error inserting row {i}: {e}", flush=True)
                print(f"      Row data: {row[:3]}...", flush=True)  # Show first 3 fields
                continue
        
        pg_conn.commit()
        print(f"  ✓ Successfully migrated {inserted}/{len(rows)} rows", flush=True)
        
    except Exception as e:
        print(f"  ❌ Error migrating table {table_name}: {e}", flush=True)
        import traceback
        traceback.print_exc()
        try:
            pg_conn.rollback()
        except:
            pass  # Connection might already be closed

# Clear ALL existing data from PostgreSQL tables BEFORE migration
print("\n" + "="*70, flush=True)
print("CLEARING EXISTING DATA FROM POSTGRESQL TABLES", flush=True)
print("="*70, flush=True)

# Get all tables from PostgreSQL
pg_cursor.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_type = 'BASE TABLE'
    ORDER BY table_name;
""")
pg_tables = [row[0] for row in pg_cursor.fetchall()]

cleared_count = 0
for pg_table in pg_tables:
    try:
        # Disable foreign key checks temporarily (PostgreSQL doesn't have this, but we use CASCADE)
        pg_cursor.execute(f"TRUNCATE TABLE {pg_table} CASCADE")
        cleared_count += 1
        print(f"  ✓ Cleared table: {pg_table}", flush=True)
    except Exception as e:
        print(f"  ⚠️  Could not clear table {pg_table}: {e}", flush=True)
        pg_conn.rollback()

pg_conn.commit()
print(f"\n✓ Cleared {cleared_count}/{len(pg_tables)} PostgreSQL tables", flush=True)
print("="*70 + "\n", flush=True)

# Now migrate each table
print("Starting data migration...\n", flush=True)
success_count = 0
for table in tables:
    try:
        migrate_table(table)
        success_count += 1
    except Exception as e:
        print(f"❌ Failed to migrate {table}: {e}", flush=True)

print(f"\n{'='*70}", flush=True)
print(f"MIGRATION COMPLETE", flush=True)
print(f"{'='*70}", flush=True)
print(f"Successfully migrated {success_count}/{len(tables)} tables", flush=True)

# Close connections
sqlite_conn.close()
pg_cursor.close()
pg_conn.close()

print("\n✓ Connections closed", flush=True)
print("\n" + "="*70, flush=True)
print("IMPORTANT: Database Tables Need to Exist First!", flush=True)
print("="*70, flush=True)
print("\nIf migration failed because tables don't exist:", flush=True)
print("1. Deploy your backend to Render first (tables will be created on first startup)", flush=True)
print("2. OR manually create tables in PostgreSQL using a compatible schema", flush=True)
print("3. Then run this migration script again", flush=True)
print("\nNext steps:", flush=True)
print("1. If tables were created, verify data in Render PostgreSQL database", flush=True)
print("2. Make sure DATABASE_URL is set correctly in Render dashboard", flush=True)
print("3. Restart your Render backend service", flush=True)


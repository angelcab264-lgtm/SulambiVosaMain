#!/usr/bin/env python3
"""
Clear and re-migrate only the externalEvents table
Run this after fixing column types to TEXT
"""

import sys
import os
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

# PostgreSQL connection
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL environment variable not set!", flush=True)
    sys.exit(1)

try:
    import psycopg2
    import sqlite3
except ImportError:
    print("❌ ERROR: psycopg2 not installed. Install with: pip install psycopg2-binary", flush=True)
    sys.exit(1)

print("=" * 70, flush=True)
print("RE-MIGRATING EXTERNAL EVENTS TABLE", flush=True)
print("=" * 70, flush=True)

# Connect to PostgreSQL
result = urlparse(DATABASE_URL)
pg_conn = psycopg2.connect(
    database=result.path[1:],
    user=result.username,
    password=result.password,
    host=result.hostname,
    port=result.port or 5432
)
pg_cursor = pg_conn.cursor()

# Connect to SQLite
sqlite_conn = sqlite3.connect(DB_PATH)
sqlite_cursor = sqlite_conn.cursor()

table_name = "externalEvents"
actual_table_name = "externalEvents"  # Should be case-sensitive

# Clear the table
print(f"\nClearing table: {actual_table_name}...", flush=True)
try:
    pg_cursor.execute(f'TRUNCATE TABLE "{actual_table_name}" RESTART IDENTITY CASCADE')
    pg_conn.commit()
    print(f"  ✓ Cleared table: {actual_table_name}", flush=True)
except Exception as e:
    pg_conn.rollback()
    try:
        pg_cursor.execute(f'DELETE FROM "{actual_table_name}"')
        pg_conn.commit()
        print(f"  ✓ Cleared table: {actual_table_name} (using DELETE)", flush=True)
    except Exception as e2:
        print(f"  ❌ Error clearing table: {e2}", flush=True)
        sys.exit(1)

# Get data from SQLite
print(f"\nGetting data from SQLite...", flush=True)
sqlite_cursor.execute(f"SELECT * FROM {table_name}")
rows = sqlite_cursor.fetchall()

if len(rows) == 0:
    print("  ⚠️  No data in SQLite table", flush=True)
    sys.exit(0)

# Get column names
sqlite_cursor.execute(f"PRAGMA table_info({table_name})")
columns = sqlite_cursor.fetchall()
column_names = [col[1] for col in columns]

print(f"  Found {len(rows)} rows to migrate", flush=True)
print(f"  Found {len(column_names)} columns", flush=True)

# Get PostgreSQL column types
pg_cursor.execute("""
    SELECT LOWER(column_name), data_type, character_maximum_length
    FROM information_schema.columns 
    WHERE LOWER(table_name) = LOWER(%s)
    ORDER BY ordinal_position
""", (actual_table_name,))
pg_results = pg_cursor.fetchall()

pg_columns = {}
pg_column_lengths = {}
for row in pg_results:
    col_name_lower = row[0]
    data_type = row[1]
    max_length = row[2]
    pg_columns[col_name_lower] = data_type
    if max_length:
        pg_column_lengths[col_name_lower] = max_length

print(f"  ✓ Found {len(pg_columns)} PostgreSQL columns", flush=True)

# Insert data
print(f"\nInserting data...", flush=True)
placeholders = ', '.join(['%s'] * len(column_names))
column_names_str = ', '.join(column_names)

inserted = 0
for i, row in enumerate(rows, 1):
    values = []
    for col_name, val in zip(column_names, row):
        col_name_lower = col_name.lower()
        pg_col_type = pg_columns.get(col_name_lower, '').upper()
        
        # Handle string values - check for VARCHAR length limits
        if isinstance(val, str):
            max_length = pg_column_lengths.get(col_name_lower)
            if max_length is not None:
                # Column has a length limit (VARCHAR)
                if len(val) > max_length:
                    print(f"      Warning: Value for column '{col_name}' ({len(val)} chars) exceeds VARCHAR({max_length}) limit", flush=True)
                    print(f"      Truncating to {max_length} characters...", flush=True)
                    val = val[:max_length]
            # TEXT columns have no limit, so we can use the full value
        values.append(val)
    
    try:
        pg_cursor.execute(
            f'INSERT INTO "{actual_table_name}" ({column_names_str}) VALUES ({placeholders})',
            values
        )
        inserted += 1
        if i % 10 == 0 or i == len(rows):
            print(f"  Progress: {i}/{len(rows)} rows ({i/len(rows)*100:.1f}%) - {inserted} inserted", flush=True)
    except Exception as e:
        print(f"  ⚠️  Error inserting row {i}: {e}", flush=True)
        pg_conn.rollback()
        continue

pg_conn.commit()
print(f"\n✓ Successfully migrated {inserted}/{len(rows)} rows", flush=True)

# Close connections
sqlite_conn.close()
pg_cursor.close()
pg_conn.close()

print("\n" + "=" * 70, flush=True)
print("RE-MIGRATION COMPLETE", flush=True)
print("=" * 70, flush=True)




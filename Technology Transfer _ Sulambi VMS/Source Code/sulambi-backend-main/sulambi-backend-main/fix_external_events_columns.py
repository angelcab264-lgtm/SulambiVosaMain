#!/usr/bin/env python3
"""
Fix externalEvents table columns to use TEXT instead of VARCHAR(255)
This allows storing longer values without truncation.
"""

import sys
import os
from dotenv import load_dotenv

# Fix Unicode encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL or not DATABASE_URL.startswith('postgresql://'):
    print("❌ DATABASE_URL not set or not a PostgreSQL URL", flush=True)
    print("Please set DATABASE_URL environment variable", flush=True)
    sys.exit(1)

try:
    import psycopg2
    from urllib.parse import urlparse
except ImportError:
    print("❌ psycopg2 not installed. Install with: pip install psycopg2-binary", flush=True)
    sys.exit(1)

print("=" * 70, flush=True)
print("FIXING EXTERNAL EVENTS TABLE COLUMNS", flush=True)
print("=" * 70, flush=True)
print(f"Connecting to PostgreSQL database...", flush=True)

try:
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
except Exception as e:
    print(f"❌ Error connecting to PostgreSQL: {e}", flush=True)
    sys.exit(1)

# Columns to change from VARCHAR(255) to TEXT
columns_to_fix = [
    'orgInvolved',
    'programInvolved',
    'projectLeader',
    'partners',
    'beneficiaries'
]

# Find the actual table name (case-sensitive)
pg_cursor.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE LOWER(table_name) = LOWER('externalEvents')
    AND table_schema = 'public';
""")
result = pg_cursor.fetchone()

if not result:
    print("❌ Table 'externalEvents' not found in PostgreSQL!", flush=True)
    pg_conn.close()
    sys.exit(1)

actual_table_name = result[0]
print(f"\nFound table: '{actual_table_name}'", flush=True)

print(f"\nFixing columns in table: {actual_table_name}", flush=True)
print("-" * 70, flush=True)

for col in columns_to_fix:
    try:
        # Check current type (case-insensitive search)
        pg_cursor.execute("""
            SELECT data_type, character_maximum_length, column_name
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND LOWER(table_name) = LOWER(%s) 
            AND LOWER(column_name) = LOWER(%s);
        """, (actual_table_name, col))
        current_info = pg_cursor.fetchone()
        
        if not current_info:
            print(f"  ⚠️  Column '{col}' does not exist, skipping...", flush=True)
            continue
        
        # Get the actual column name (case-sensitive)
        actual_col_name = current_info[2]
        
        current_type = current_info[0]
        max_length = current_info[1]
        
        if current_type.upper() == 'TEXT' or (current_type.upper() == 'CHARACTER VARYING' and max_length is None):
            print(f"  ✓ Column '{col}' is already TEXT", flush=True)
            continue
        
        if current_type.upper() == 'CHARACTER VARYING' and max_length == 255:
            # Alter column type to TEXT (use actual column name for case-sensitive PostgreSQL)
            pg_cursor.execute(f'ALTER TABLE "{actual_table_name}" ALTER COLUMN "{actual_col_name}" TYPE TEXT USING "{actual_col_name}"::TEXT')
            pg_conn.commit()
            if actual_col_name != col:
                print(f"  ✓ Changed column '{actual_col_name}' (requested: '{col}') from VARCHAR(255) to TEXT", flush=True)
            else:
                print(f"  ✓ Changed column '{col}' from VARCHAR(255) to TEXT", flush=True)
        else:
            print(f"  ⚠️  Column '{col}' has unexpected type: {current_type} (max_length: {max_length})", flush=True)
            print(f"      Skipping...", flush=True)
    except Exception as e:
        pg_conn.rollback()
        print(f"  ❌ Error fixing column '{col}': {e}", flush=True)

print("\n" + "=" * 70, flush=True)
print("✓ Column type fixes completed!", flush=True)
print("=" * 70, flush=True)

pg_cursor.close()
pg_conn.close()


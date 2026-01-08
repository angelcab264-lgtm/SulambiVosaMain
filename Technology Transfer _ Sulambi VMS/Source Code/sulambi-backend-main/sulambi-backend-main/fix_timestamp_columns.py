#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix timestamp columns in PostgreSQL to use BIGINT instead of INTEGER
Run this BEFORE running the migration script if you get "integer out of range" errors
"""

import os
import sys
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL environment variable not set!")
    sys.exit(1)

try:
    import psycopg2
    result = urlparse(DATABASE_URL)
    
    db_name = result.path[1:] if result.path.startswith('/') else result.path
    db_user = result.username
    db_password = result.password
    db_host = result.hostname
    db_port = result.port or 5432
    
    print("=" * 70)
    print("FIXING TIMESTAMP COLUMNS IN POSTGRESQL")
    print("=" * 70)
    print(f"Connecting to: {db_host}:{db_port}/{db_name}")
    
    pg_conn = psycopg2.connect(
        database=db_name,
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port,
        connect_timeout=10
    )
    pg_cursor = pg_conn.cursor()
    print("✓ Connected to PostgreSQL database\n")
    
    # List all tables to help debug
    pg_cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """)
    all_tables = [row[0] for row in pg_cursor.fetchall()]
    print(f"Found {len(all_tables)} tables in database:")
    for tbl in all_tables:
        print(f"  - {tbl}")
    print()
    
    # Columns that need to be changed from INTEGER to BIGINT
    tables_to_fix = {
        'internalEvents': ['durationStart', 'durationEnd', 'evaluationSendTime'],
        'externalEvents': ['durationStart', 'durationEnd', 'evaluationSendTime']
    }
    
    for table_name, columns in tables_to_fix.items():
        print(f"Fixing table: {table_name}")
        
        # Check if table exists (case-insensitive)
        pg_cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE LOWER(table_name) = LOWER(%s)
            AND table_schema = 'public'
        """, (table_name,))
        result = pg_cursor.fetchone()
        
        if not result:
            print(f"  ⚠️  Table '{table_name}' does not exist, skipping...\n")
            continue
        
        # Use the actual table name from database (might have different case)
        actual_table_name = result[0]
        if actual_table_name != table_name:
            print(f"  → Found table as '{actual_table_name}' (case difference)")
        
        for column_name in columns:
            try:
                # Check current column type (case-insensitive)
                pg_cursor.execute("""
                    SELECT data_type, column_name
                    FROM information_schema.columns 
                    WHERE LOWER(table_name) = LOWER(%s) AND LOWER(column_name) = LOWER(%s)
                """, (actual_table_name, column_name))
                result = pg_cursor.fetchone()
                
                if not result:
                    print(f"  ⚠️  Column '{column_name}' does not exist, skipping...")
                    continue
                
                current_type = result[0]
                actual_column_name = result[1]
                
                if current_type.upper() == 'BIGINT':
                    print(f"  ✓ Column '{actual_column_name}' is already BIGINT")
                elif current_type.upper() == 'INTEGER':
                    print(f"  → Converting '{actual_column_name}' from INTEGER to BIGINT...")
                    pg_cursor.execute(f'ALTER TABLE "{actual_table_name}" ALTER COLUMN "{actual_column_name}" TYPE BIGINT USING "{actual_column_name}"::BIGINT')
                    pg_conn.commit()
                    print(f"  ✓ Successfully converted '{actual_column_name}' to BIGINT")
                else:
                    print(f"  ⚠️  Column '{actual_column_name}' is {current_type}, not INTEGER. Skipping...")
                    
            except Exception as e:
                print(f"  ❌ Error fixing column '{column_name}': {e}")
                pg_conn.rollback()
        
        print()
    
    print("=" * 70)
    print("DONE")
    print("=" * 70)
    print("\nYou can now run the migration script.")
    
    pg_cursor.close()
    pg_conn.close()
    
except ImportError:
    print("❌ ERROR: psycopg2 not installed. Install with: pip install psycopg2-binary")
    sys.exit(1)
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


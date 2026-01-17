#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Detailed check of Render PostgreSQL database
Shows all tables with row counts and sample data
"""

import os
import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL environment variable not set!", flush=True)
    sys.exit(1)

try:
    import psycopg2
    result = urlparse(DATABASE_URL)
    
    print("=" * 70, flush=True)
    print("DETAILED RENDER POSTGRESQL DATABASE CHECK", flush=True)
    print("=" * 70, flush=True)
    print(f"Host: {result.hostname}", flush=True)
    print(f"Database: {result.path[1:]}", flush=True)
    print("=" * 70, flush=True)
    
    conn = psycopg2.connect(
        database=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port or 5432
    )
    cursor = conn.cursor()
    print("✓ Connected successfully!\n", flush=True)
    
    # Get all tables
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = cursor.fetchall()
    
    print(f"Found {len(tables)} tables:\n", flush=True)
    
    # Check each table for data
    total_rows = 0
    tables_with_data = []
    tables_empty = []
    
    for (table_name,) in tables:
        try:
            # Quote table name to preserve case
            cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
            count = cursor.fetchone()[0]
            total_rows += count
            
            if count > 0:
                status = "✅"
                tables_with_data.append((table_name, count))
                print(f"  {status} {table_name:35} {count:>6} rows", flush=True)
            else:
                status = "⚪"
                tables_empty.append(table_name)
                print(f"  {status} {table_name:35} {count:>6} rows (empty)", flush=True)
        except Exception as e:
            print(f"  ❌ {table_name:35} Error: {str(e)[:50]}", flush=True)
            # Rollback to continue checking other tables
            try:
                conn.rollback()
            except:
                pass
    
    print("\n" + "=" * 70, flush=True)
    print(f"SUMMARY", flush=True)
    print("=" * 70, flush=True)
    print(f"Total tables: {len(tables)}", flush=True)
    print(f"Tables with data: {len(tables_with_data)}", flush=True)
    print(f"Empty tables: {len(tables_empty)}", flush=True)
    print(f"Total rows: {total_rows:,}", flush=True)
    
    if tables_with_data:
        print("\n" + "=" * 70, flush=True)
        print("TABLES WITH DATA (sorted by row count)", flush=True)
        print("=" * 70, flush=True)
        for table_name, count in sorted(tables_with_data, key=lambda x: x[1], reverse=True):
            print(f"  {table_name:35} {count:>6,} rows", flush=True)
    
    if tables_empty:
        print("\n" + "=" * 70, flush=True)
        print("EMPTY TABLES", flush=True)
        print("=" * 70, flush=True)
        for table_name in sorted(tables_empty):
            print(f"  {table_name}", flush=True)
    
    # Show sample data from key tables
    print("\n" + "=" * 70, flush=True)
    print("SAMPLE DATA FROM KEY TABLES", flush=True)
    print("=" * 70, flush=True)
    
    key_tables = ['accounts', 'membership', 'internalEvents', 'externalEvents', 'requirements', 'evaluation']
    for table in key_tables:
        try:
            cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
            count = cursor.fetchone()[0]
            if count > 0:
                print(f"\n{table}:", flush=True)
                # Get column names
                cursor.execute(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = %s 
                    AND table_schema = 'public'
                    ORDER BY ordinal_position
                    LIMIT 5
                """, (table,))
                columns = [row[0] for row in cursor.fetchall()]
                col_str = ', '.join([f'"{col}"' for col in columns])
                
                # Get first row
                cursor.execute(f'SELECT {col_str} FROM "{table}" LIMIT 1')
                row = cursor.fetchone()
                if row:
                    print(f"  Sample row (first {len(columns)} columns):", flush=True)
                    for col, val in zip(columns, row):
                        val_str = str(val)[:50] if val else "NULL"
                        print(f"    {col}: {val_str}", flush=True)
        except Exception as e:
            print(f"  {table}: Error - {e}", flush=True)
            try:
                conn.rollback()
            except:
                pass
    
    print("\n" + "=" * 70, flush=True)
    print("✅ DATABASE CHECK COMPLETE", flush=True)
    print("=" * 70, flush=True)
    
    cursor.close()
    conn.close()
    
except ImportError:
    print("❌ ERROR: psycopg2 not installed. Install with: pip install psycopg2-binary", flush=True)
    sys.exit(1)
except Exception as e:
    print(f"❌ ERROR connecting to database: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)
















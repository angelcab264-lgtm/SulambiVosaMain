#!/usr/bin/env python3
"""
View the Render PostgreSQL database contents
Run this locally with DATABASE_URL set to your Render database connection string
"""

import os
import sys
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL environment variable not set!")
    print("\nTo get your DATABASE_URL:")
    print("1. Go to Render Dashboard → sulambi-database")
    print("2. Click on 'Connection Info' tab")
    print("3. Copy the 'Internal Database URL'")
    print("\nThen set it as:")
    print("  Windows PowerShell: $env:DATABASE_URL = 'your-connection-string'")
    print("  Or create a .env file with: DATABASE_URL=your-connection-string")
    sys.exit(1)

try:
    import psycopg2
    result = urlparse(DATABASE_URL)
    
    print("=" * 70)
    print("CONNECTING TO RENDER POSTGRESQL DATABASE")
    print("=" * 70)
    print(f"Host: {result.hostname}")
    print(f"Database: {result.path[1:]}")
    print(f"User: {result.username}")
    print("=" * 70)
    
    conn = psycopg2.connect(
        database=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port or 5432
    )
    cursor = conn.cursor()
    print("✓ Connected successfully!\n")
    
    # Get all tables
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
    """)
    tables = cursor.fetchall()
    
    print(f"Found {len(tables)} tables:\n")
    
    # Show data for each table
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        
        print(f"📊 {table_name}: {count} rows")
        
        # Show first few rows if table has data
        if count > 0 and count <= 10:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
            rows = cursor.fetchall()
            
            # Get column names
            cursor.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position;
            """)
            columns = [col[0] for col in cursor.fetchall()]
            
            print(f"   Columns: {', '.join(columns[:5])}{'...' if len(columns) > 5 else ''}")
            
            if rows:
                print(f"   Sample data (first row):")
                print(f"   {dict(zip(columns, rows[0]))}")
        print()
    
    # Summary statistics
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    # Check key tables
    key_tables = ['accounts', 'membership', 'requirements', 'evaluation', 'internalEvents', 'externalEvents']
    for table in key_tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count} records")
        except:
            print(f"  {table}: table does not exist")
    
    cursor.close()
    conn.close()
    print("\n✓ Connection closed")
    
except ImportError:
    print("❌ ERROR: psycopg2 not installed")
    print("Install with: pip install psycopg2-binary")
    sys.exit(1)
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


#!/usr/bin/env python3
"""
Check which tables the migration script will use to store data
This verifies the table name mapping from SQLite to PostgreSQL
"""

import sys
import os
import sqlite3
from dotenv import load_dotenv
from urllib.parse import urlparse

# Fix Unicode encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

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

print("=" * 70, flush=True)
print("CHECKING MIGRATION TARGET TABLES", flush=True)
print("=" * 70, flush=True)

# Connect to SQLite
if not os.path.exists(DB_PATH):
    print(f"❌ ERROR: SQLite database not found at: {DB_PATH}", flush=True)
    sys.exit(1)

sqlite_conn = sqlite3.connect(DB_PATH)
sqlite_cursor = sqlite_conn.cursor()

# Get SQLite tables
sqlite_cursor.execute("""
    SELECT name FROM sqlite_master 
    WHERE type='table' AND name NOT LIKE 'sqlite_%'
    ORDER BY name
""")
sqlite_tables = [row[0] for row in sqlite_cursor.fetchall()]

print(f"\nFound {len(sqlite_tables)} tables in SQLite:", flush=True)
for table in sqlite_tables:
    sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = sqlite_cursor.fetchone()[0]
    print(f"  - {table} ({count} rows)", flush=True)

# Connect to PostgreSQL
try:
    import psycopg2
    result = urlparse(DATABASE_URL)
    pg_conn = psycopg2.connect(
        database=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port or 5432
    )
    pg_cursor = pg_conn.cursor()
except ImportError:
    print("❌ ERROR: psycopg2 not installed. Install with: pip install psycopg2-binary", flush=True)
    sys.exit(1)
except Exception as e:
    print(f"❌ ERROR connecting to PostgreSQL: {e}", flush=True)
    sys.exit(1)

# Get PostgreSQL tables
pg_cursor.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public'
    AND table_type = 'BASE TABLE'
    ORDER BY table_name
""")
pg_tables_list = [row[0] for row in pg_cursor.fetchall()]

# Create mapping (same logic as migration script)
table_name_mapping = {}
for sqlite_table in sqlite_tables:
    # Find matching PostgreSQL table (case-insensitive)
    for pg_table in pg_tables_list:
        if sqlite_table.lower() == pg_table.lower():
            table_name_mapping[sqlite_table] = pg_table
            break
    # If no match found, use SQLite name as-is
    if sqlite_table not in table_name_mapping:
        table_name_mapping[sqlite_table] = sqlite_table

print(f"\nFound {len(pg_tables_list)} tables in PostgreSQL", flush=True)

# Show mapping
print("\n" + "=" * 70, flush=True)
print("MIGRATION TABLE MAPPING (SQLite -> PostgreSQL)", flush=True)
print("=" * 70, flush=True)
print("\nThis shows where the migration script will store data:\n", flush=True)

for sqlite_name in sorted(sqlite_tables):
    pg_name = table_name_mapping.get(sqlite_name, sqlite_name)
    
    # Check if table exists in PostgreSQL
    if pg_name in pg_tables_list:
        # Check row count
        try:
            pg_cursor.execute(f'SELECT COUNT(*) FROM "{pg_name}"')
            pg_count = pg_cursor.fetchone()[0]
        except:
            pg_count = "?"
        
        if sqlite_name != pg_name:
            print(f"  {sqlite_name:30} -> {pg_name:30} (case difference) [{pg_count} rows]", flush=True)
        else:
            print(f"  {sqlite_name:30} -> {pg_name:30} [{pg_count} rows]", flush=True)
    else:
        print(f"  {sqlite_name:30} -> {pg_name:30} ⚠️  TABLE NOT FOUND!", flush=True)

# Verify against application table names
print("\n" + "=" * 70, flush=True)
print("VERIFICATION: Application Table Names", flush=True)
print("=" * 70, flush=True)

app_table_names = {
    'accounts', 'sessions', 'membership', 'requirements',
    'internalEvents', 'externalEvents', 'internalReport', 'externalReport',
    'helpdesk', 'evaluation', 'eventSignatories', 'feedback',
    'activity_month_assignments', 'satisfactionSurveys',
    'dropoutRiskAssessment', 'volunteerParticipationHistory',
    'semester_satisfaction'
}

print("\nChecking if migration targets match application expectations:\n", flush=True)
all_match = True
for sqlite_name in sorted(sqlite_tables):
    pg_name = table_name_mapping.get(sqlite_name, sqlite_name)
    
    if sqlite_name in app_table_names:
        if pg_name == sqlite_name:
            print(f"  ✓ {sqlite_name:30} -> {pg_name:30} (matches app)", flush=True)
        elif pg_name.lower() == sqlite_name.lower():
            print(f"  ⚠️  {sqlite_name:30} -> {pg_name:30} (case difference, but app uses: {sqlite_name})", flush=True)
            all_match = False
        else:
            print(f"  ❌ {sqlite_name:30} -> {pg_name:30} (MISMATCH!)", flush=True)
            all_match = False

if all_match:
    print("\n✓ All tables will be migrated to the correct tables that the application uses!", flush=True)
else:
    print("\n⚠️  Some tables may be migrated to different names than the application expects!", flush=True)

# Close connections
sqlite_conn.close()
pg_cursor.close()
pg_conn.close()

print("\n" + "=" * 70, flush=True)
print("DONE", flush=True)
print("=" * 70, flush=True)







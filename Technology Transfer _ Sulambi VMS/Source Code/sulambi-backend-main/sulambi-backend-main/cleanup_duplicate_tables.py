#!/usr/bin/env python3
"""
Clean up duplicate lowercase tables in PostgreSQL
This script drops the lowercase duplicate tables that the application doesn't use
"""

import sys
import os
from dotenv import load_dotenv
from urllib.parse import urlparse

# Fix Unicode encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL or not DATABASE_URL.startswith('postgresql://'):
    print("❌ DATABASE_URL not set or not a PostgreSQL URL", flush=True)
    sys.exit(1)

try:
    import psycopg2
except ImportError:
    print("❌ psycopg2 not installed. Install with: pip install psycopg2-binary", flush=True)
    sys.exit(1)

print("=" * 70, flush=True)
print("CLEANING UP DUPLICATE TABLES", flush=True)
print("=" * 70, flush=True)

# Tables the application uses (correct case)
app_tables = {
    'accounts',
    'sessions',
    'membership',
    'requirements',
    'internalEvents',
    'externalEvents',
    'internalReport',
    'externalReport',
    'helpdesk',
    'evaluation',
    'eventSignatories',
    'feedback',
    'activity_month_assignments',
    'satisfactionSurveys',
    'dropoutRiskAssessment',
    'volunteerParticipationHistory',
    'semester_satisfaction'
}

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

# Get all tables
pg_cursor.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public'
    ORDER BY table_name
""")
all_tables = {row[0] for row in pg_cursor.fetchall()}

# Find duplicate tables (same name, different case)
table_names_lower = {}
for table in all_tables:
    lower = table.lower()
    if lower not in table_names_lower:
        table_names_lower[lower] = []
    table_names_lower[lower].append(table)

# Find duplicates and identify which ones to drop
tables_to_drop = []
for lower_name, variants in table_names_lower.items():
    if len(variants) > 1:
        # Find which one the app uses
        app_match = None
        for variant in variants:
            if variant in app_tables:
                app_match = variant
                break
        
        if app_match:
            # Drop the ones that don't match
            for variant in variants:
                if variant != app_match:
                    tables_to_drop.append(variant)
        else:
            # None match app tables - keep the one with proper case (camelCase)
            # Drop all lowercase ones
            for variant in variants:
                if variant.islower():
                    tables_to_drop.append(variant)

if not tables_to_drop:
    print("\n✓ No duplicate tables to clean up!", flush=True)
    pg_cursor.close()
    pg_conn.close()
    sys.exit(0)

print(f"\nFound {len(tables_to_drop)} duplicate tables to drop:", flush=True)
for table in sorted(tables_to_drop):
    print(f"  - {table}", flush=True)

print("\n⚠️  WARNING: This will permanently delete these tables!", flush=True)
print("Make sure they are empty or contain no important data.", flush=True)
response = input("\nContinue? (yes/no): ")
if response.lower() not in ['yes', 'y']:
    print("Cancelled.", flush=True)
    pg_cursor.close()
    pg_conn.close()
    sys.exit(0)

# Check if tables are empty before dropping
print("\nChecking if tables are empty...", flush=True)
tables_with_data = []
for table in tables_to_drop:
    try:
        pg_cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
        count = pg_cursor.fetchone()[0]
        if count > 0:
            tables_with_data.append((table, count))
            print(f"  ⚠️  Table '{table}' has {count} rows", flush=True)
        else:
            print(f"  ✓ Table '{table}' is empty", flush=True)
    except Exception as e:
        print(f"  ⚠️  Could not check table '{table}': {e}", flush=True)

if tables_with_data:
    print(f"\n⚠️  WARNING: {len(tables_with_data)} tables contain data!", flush=True)
    print("These tables will NOT be dropped for safety.", flush=True)
    tables_to_drop = [t for t in tables_to_drop if t not in [tbl for tbl, _ in tables_with_data]]
    
    if not tables_to_drop:
        print("\nNo empty duplicate tables to drop.", flush=True)
        pg_cursor.close()
        pg_conn.close()
        sys.exit(0)

# Drop empty duplicate tables
print(f"\nDropping {len(tables_to_drop)} empty duplicate tables...", flush=True)
dropped_count = 0
for table in tables_to_drop:
    try:
        pg_cursor.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')
        pg_conn.commit()
        print(f"  ✓ Dropped table: {table}", flush=True)
        dropped_count += 1
    except Exception as e:
        pg_conn.rollback()
        print(f"  ❌ Error dropping table '{table}': {e}", flush=True)

print(f"\n✓ Successfully dropped {dropped_count}/{len(tables_to_drop)} tables", flush=True)

if tables_with_data:
    print(f"\n⚠️  {len(tables_with_data)} tables were NOT dropped because they contain data:", flush=True)
    for table, count in tables_with_data:
        print(f"  - {table} ({count} rows)", flush=True)
    print("\nIf you want to drop these, you'll need to do it manually.", flush=True)

pg_cursor.close()
pg_conn.close()

print("\n" + "=" * 70, flush=True)
print("CLEANUP COMPLETE", flush=True)
print("=" * 70, flush=True)
















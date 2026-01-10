#!/usr/bin/env python3
"""
Re-migrate externalEvents table after fixing column types
This script clears and re-migrates only the externalEvents table
"""

import sys
import os

# Import the migration function from the main script
sys.path.insert(0, os.path.dirname(__file__))

# Import necessary parts from migrate_sqlite_to_postgresql.py
from migrate_sqlite_to_postgresql import (
    sqlite_conn, sqlite_cursor, pg_conn, pg_cursor,
    table_name_mapping, migrate_table
)

print("=" * 70, flush=True)
print("RE-MIGRATING EXTERNAL EVENTS TABLE", flush=True)
print("=" * 70, flush=True)
print("\nThis will:", flush=True)
print("1. Clear the externalEvents table in PostgreSQL", flush=True)
print("2. Re-migrate all data from SQLite", flush=True)
print("\nMake sure you've run fix_external_events_columns.py first!", flush=True)
print("=" * 70, flush=True)

response = input("\nContinue? (yes/no): ")
if response.lower() not in ['yes', 'y']:
    print("Cancelled.", flush=True)
    sys.exit(0)

table_name = "externalEvents"
actual_table_name = table_name_mapping.get(table_name, table_name)

# Clear the table
print(f"\nClearing table: {actual_table_name}...", flush=True)
try:
    # Try TRUNCATE first
    try:
        pg_cursor.execute(f'TRUNCATE TABLE "{actual_table_name}" RESTART IDENTITY CASCADE')
        pg_conn.commit()
        print(f"  ✓ Cleared table: {actual_table_name}", flush=True)
    except Exception as e1:
        # Fallback to DELETE
        pg_conn.rollback()
        pg_cursor.execute(f'DELETE FROM "{actual_table_name}"')
        pg_conn.commit()
        print(f"  ✓ Cleared table: {actual_table_name} (using DELETE)", flush=True)
except Exception as e:
    pg_conn.rollback()
    print(f"  ❌ Error clearing table: {e}", flush=True)
    sys.exit(1)

# Re-migrate
print(f"\nRe-migrating table: {table_name}...", flush=True)
try:
    success, rows_migrated, total_rows = migrate_table(table_name, test_mode=False)
    if success:
        print(f"\n✓ Successfully re-migrated {rows_migrated} rows", flush=True)
    else:
        print(f"\n❌ Migration failed", flush=True)
        sys.exit(1)
except Exception as e:
    print(f"\n❌ Error during migration: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70, flush=True)
print("RE-MIGRATION COMPLETE", flush=True)
print("=" * 70, flush=True)





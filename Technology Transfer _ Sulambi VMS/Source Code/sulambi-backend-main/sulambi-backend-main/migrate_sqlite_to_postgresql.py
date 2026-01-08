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
    
    # Extract connection parameters
    db_name = result.path[1:] if result.path.startswith('/') else result.path
    db_user = result.username
    db_password = result.password
    db_host = result.hostname
    db_port = result.port or 5432
    
    print(f"Connecting to: {db_host}:{db_port}/{db_name}", flush=True)
    print(f"User: {db_user}", flush=True)
    
    # Try to connect with retry
    import time
    max_retries = 3
    for attempt in range(max_retries):
        try:
            pg_conn = psycopg2.connect(
                database=db_name,
                user=db_user,
                password=db_password,
                host=db_host,
                port=db_port,
                connect_timeout=10,
                options='-c statement_timeout=300000'  # 5 minute timeout for queries
            )
            pg_cursor = pg_conn.cursor()
            print("✓ Connected to PostgreSQL database", flush=True)
            break
        except Exception as conn_error:
            if attempt < max_retries - 1:
                print(f"  Connection attempt {attempt + 1} failed, retrying...", flush=True)
                time.sleep(2)
            else:
                raise conn_error
                
except ImportError:
    print("❌ ERROR: psycopg2 not installed. Install with: pip install psycopg2-binary", flush=True)
    sys.exit(1)
except Exception as e:
    print(f"❌ ERROR connecting to PostgreSQL: {e}", flush=True)
    print(f"\nTroubleshooting:", flush=True)
    print(f"1. Verify the External Database URL is correct in Render Dashboard", flush=True)
    print(f"2. Check your internet connection", flush=True)
    print(f"3. Try using the IP address instead: {db_host}", flush=True)
    print(f"4. Verify the database is running on Render", flush=True)
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
sqlite_tables = [row[0] for row in sqlite_cursor.fetchall()]

# Get all tables from PostgreSQL to create a case-sensitive mapping
pg_cursor.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_type = 'BASE TABLE'
    ORDER BY table_name
""")
pg_tables_list = [row[0] for row in pg_cursor.fetchall()]

# Create a mapping from SQLite table names (case-insensitive) to PostgreSQL table names (exact case)
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

print(f"\nFound {len(sqlite_tables)} tables to migrate from SQLite", flush=True)
print(f"Found {len(pg_tables_list)} tables in PostgreSQL", flush=True)
print(f"\nTable name mapping (SQLite -> PostgreSQL):", flush=True)
for sqlite_name, pg_name in sorted(table_name_mapping.items()):
    if sqlite_name != pg_name:
        print(f"  {sqlite_name} -> {pg_name} (case difference)", flush=True)
    else:
        print(f"  {sqlite_name} -> {pg_name}", flush=True)
print(f"\nStarting migration...\n", flush=True)

# Use SQLite table names for iteration, but map to PostgreSQL names when needed
tables = sqlite_tables

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

def migrate_table(table_name, test_mode=False, limit_rows=None):
    """Migrate a single table from SQLite to PostgreSQL
    
    Args:
        table_name: Name of the table to migrate
        test_mode: If True, only migrate first 5 rows (or limit_rows if specified)
        limit_rows: Number of rows to migrate (overrides test_mode default of 5)
    Returns:
        tuple: (success: bool, rows_migrated: int, total_rows: int)
    """
    test_label = " [TEST MODE - 5 rows]" if test_mode and limit_rows is None else f" [TEST MODE - {limit_rows} rows]" if limit_rows else ""
    print(f"\n{'='*70}", flush=True)
    print(f"Migrating table: {table_name}{test_label}", flush=True)
    print(f"{'='*70}", flush=True)
    
    try:
        # Get table structure
        columns = get_columns(sqlite_cursor, table_name)
        print(f"  Found {len(columns)} columns", flush=True)
        
        # Get total row count first
        sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_rows_in_db = sqlite_cursor.fetchone()[0]
        
        if total_rows_in_db == 0:
            print(f"  ⚠️  Table is empty, skipping...", flush=True)
            return (True, 0, 0)
        
        # Get data from SQLite (limited if test_mode)
        if test_mode or limit_rows:
            limit = limit_rows if limit_rows else 5
            sqlite_cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
            rows = sqlite_cursor.fetchall()
            print(f"  Found {len(rows)} rows to migrate (out of {total_rows_in_db} total)", flush=True)
        else:
            sqlite_cursor.execute(f"SELECT * FROM {table_name}")
            rows = sqlite_cursor.fetchall()
            print(f"  Found {len(rows)} rows to migrate", flush=True)
        
        # Get column names
        column_names = [col[1] for col in columns]
        
        # Get the exact PostgreSQL table name from our mapping
        actual_table_name = table_name_mapping.get(table_name, table_name)
        
        # Verify the table exists with this exact name
        pg_cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = %s
                AND table_schema = 'public'
            )
        """, (actual_table_name,))
        table_exists = pg_cursor.fetchone()[0]
        
        if not table_exists:
            print(f"  ⚠️  Table '{actual_table_name}' does not exist in PostgreSQL!", flush=True)
            print(f"  ⚠️  Please run 'python server.py --init' on Render first to create tables", flush=True)
            print(f"  ⚠️  Or create tables manually in PostgreSQL", flush=True)
            return (False, 0, total_rows_in_db)
        
        # Use the exact PostgreSQL table name (case-sensitive)
        if actual_table_name != table_name:
            print(f"  → Using PostgreSQL table name '{actual_table_name}' (SQLite: '{table_name}')", flush=True)
        
        # Clear existing data for this specific table before migrating
        # First, ensure we're in a clean transaction state
        try:
            pg_conn.rollback()
        except:
            pass
        
        try:
            # First get row count (use actual table name)
            pg_cursor.execute(f'SELECT COUNT(*) FROM "{actual_table_name}"')
            count_before = pg_cursor.fetchone()[0]
            
            if count_before > 0:
                # Use TRUNCATE with RESTART IDENTITY to reset sequences
                pg_cursor.execute(f'TRUNCATE TABLE "{actual_table_name}" RESTART IDENTITY CASCADE')
                pg_conn.commit()
                
                # Verify it was cleared
                pg_cursor.execute(f'SELECT COUNT(*) FROM "{actual_table_name}"')
                count_after = pg_cursor.fetchone()[0]
                print(f"  ✓ Cleared {count_before} rows from {actual_table_name}", flush=True)
            else:
                print(f"  ✓ Table {actual_table_name} is already empty", flush=True)
        except Exception as e:
            # Rollback any failed transaction
            try:
                pg_conn.rollback()
            except:
                pass
            
            # If TRUNCATE fails, try DELETE and reset sequence manually
            try:
                pg_cursor.execute(f'SELECT COUNT(*) FROM "{actual_table_name}"')
                count_before = pg_cursor.fetchone()[0]
                
                if count_before > 0:
                    pg_cursor.execute(f'DELETE FROM "{actual_table_name}"')
                    # Reset sequence if table has SERIAL id column
                    try:
                        pg_cursor.execute(f'ALTER SEQUENCE "{actual_table_name}_id_seq" RESTART WITH 1')
                    except:
                        pass  # Sequence might not exist or have different name
                    pg_conn.commit()
                    print(f"  ✓ Cleared {count_before} rows from {actual_table_name} (using DELETE)", flush=True)
                else:
                    print(f"  ✓ Table {actual_table_name} is already empty", flush=True)
            except Exception as e2:
                # Rollback again
                try:
                    pg_conn.rollback()
                except:
                    pass
                print(f"  ⚠️  Could not clear table {actual_table_name}: {e2}", flush=True)
                # Continue anyway - might have constraints we can't handle
        
        # Get PostgreSQL column types to handle type conversion
        # Note: PostgreSQL column names are case-insensitive unless quoted
        print(f"  Getting PostgreSQL column types...", flush=True)
        try:
            # Use actual table name (case-insensitive lookup)
            # Get both column_name, data_type, and character_maximum_length for VARCHAR
            pg_cursor.execute("""
                SELECT LOWER(column_name), data_type, character_maximum_length
                FROM information_schema.columns 
                WHERE LOWER(table_name) = LOWER(%s)
                ORDER BY ordinal_position
            """, (actual_table_name,))
            results = pg_cursor.fetchall()
            
            # Store both data_type and max_length for VARCHAR columns
            pg_columns = {}
            pg_column_lengths = {}
            for row in results:
                col_name_lower = row[0]
                data_type = row[1]
                max_length = row[2]
                pg_columns[col_name_lower] = data_type
                if max_length:
                    pg_column_lengths[col_name_lower] = max_length
            
            print(f"  ✓ Found {len(pg_columns)} PostgreSQL columns", flush=True)
        except Exception as e:
            print(f"  ⚠️  Error getting column types: {e}", flush=True)
            import traceback
            traceback.print_exc()
            pg_columns = {}
            pg_column_lengths = {}
        
        # Also check for createdat/createdAt variations
        if 'createdat' in pg_columns or 'created_at' in pg_columns:
            print(f"  Found timestamp column: createdat/created_at", flush=True)
        
        # Check for columns that might have integer overflow issues
        timestamp_int_columns = ['durationstart', 'durationend', 'evaluationsendtime']
        problematic_columns = []
        for col in timestamp_int_columns:
            if col in pg_columns and pg_columns[col].upper() == 'INTEGER':
                problematic_columns.append(col)
        if problematic_columns:
            print(f"  ⚠️  Warning: Columns {problematic_columns} are INTEGER but may contain large timestamp values", flush=True)
            print(f"      These should be BIGINT in PostgreSQL. Migration may fail for these columns.", flush=True)
        
        print(f"  Starting data insertion...", flush=True)
        
        # Insert data - use savepoints for each row to handle errors gracefully
        placeholders = ', '.join(['%s'] * len(column_names))
        column_names_str = ', '.join(column_names)
        
        inserted = 0
        total_rows = len(rows)
        # Show progress every 10% or every 100 rows, whichever is smaller
        progress_interval = max(1, min(100, total_rows // 10))
        
        print(f"  Processing {total_rows} rows...", flush=True)
        
        for i, row in enumerate(rows, 1):
            try:
                # Create a savepoint for this row
                savepoint_name = f"sp_row_{i}"
                pg_cursor.execute(f"SAVEPOINT {savepoint_name}")
                
                # Convert None to NULL, handle BLOB data, and convert types
                values = []
                for idx, (col_name, val) in enumerate(zip(column_names, row)):
                    if val is None:
                        values.append(None)
                    elif isinstance(val, bytes):
                        values.append(val)
                    else:
                        col_name_lower = col_name.lower()
                        pg_col_type = pg_columns.get(col_name_lower, '').upper()
                        
                        # Convert INTEGER (0/1) to BOOLEAN for boolean columns
                        if pg_col_type == 'BOOLEAN' and isinstance(val, int):
                            values.append(bool(val))
                        # Convert TIMESTAMP columns from milliseconds to PostgreSQL timestamp
                        # Check for createdAt, createdat, created_at variations
                        elif (pg_col_type in ('TIMESTAMP WITHOUT TIME ZONE', 'TIMESTAMP') or 
                              col_name_lower in ('createdat', 'created_at')) and isinstance(val, (int, float)):
                            from datetime import datetime
                            try:
                                # SQLite stores timestamps as milliseconds (Unix timestamp * 1000)
                                # Check if it's milliseconds (typically > 1e12) or seconds
                                if val > 1e12:  # Definitely milliseconds (after year 2001)
                                    values.append(datetime.fromtimestamp(val / 1000.0))
                                elif val > 1e9:  # Could be milliseconds or seconds after 2001
                                    # Try as milliseconds first
                                    try:
                                        values.append(datetime.fromtimestamp(val / 1000.0))
                                    except:
                                        values.append(datetime.fromtimestamp(val))
                                else:  # Seconds
                                    values.append(datetime.fromtimestamp(val))
                            except (ValueError, OSError, OverflowError) as e:
                                print(f"      Warning: Could not convert timestamp {val} for {col_name}: {e}", flush=True)
                                values.append(None)
                        # Convert empty strings to NULL for integer/numeric columns
                        elif pg_col_type in ('INTEGER', 'BIGINT', 'SMALLINT', 'NUMERIC', 'REAL', 'DOUBLE PRECISION') and (val == '' or (isinstance(val, str) and val.strip() == '')):
                            values.append(None)
                        # Handle integer overflow - check ALL integer types, not just INTEGER
                        elif isinstance(val, int):
                            # PostgreSQL INTEGER max is 2147483647, SMALLINT max is 32767
                            if pg_col_type == 'SMALLINT':
                                if val > 32767 or val < -32768:
                                    # Value too large for SMALLINT
                                    print(f"      Warning: Value {val} exceeds SMALLINT range for column {col_name}, setting to NULL", flush=True)
                                    values.append(None)
                                else:
                                    values.append(val)
                            elif pg_col_type == 'INTEGER':
                                if val > 2147483647 or val < -2147483648:
                                    # Value exceeds INTEGER range
                                    # Check if this looks like a timestamp (milliseconds)
                                    if val > 1e12:  # Likely a timestamp in milliseconds
                                        # This should be BIGINT, but column is INTEGER
                                        # We cannot insert this value - it will fail
                                        # Skip this row with a clear error message
                                        raise ValueError(f"Column '{col_name}' is INTEGER but contains timestamp value {val} (milliseconds) which exceeds INTEGER range. This column should be BIGINT in PostgreSQL. Please update the table schema.")
                                    else:
                                        # Regular integer overflow
                                        print(f"      Warning: Integer value {val} exceeds INTEGER range for column {col_name}, setting to NULL", flush=True)
                                        values.append(None)
                                else:
                                    values.append(val)
                            elif pg_col_type == 'BIGINT':
                                # BIGINT can handle any Python int
                                values.append(val)
                            else:
                                # Unknown type or not an integer column, pass through
                                values.append(val)
                        else:
                            # Handle string values - check for VARCHAR length limits
                            if isinstance(val, str):
                                # Check if column has a length limit (from character_maximum_length)
                                max_length = pg_column_lengths.get(col_name_lower)
                                if max_length is not None:
                                    # Column has a length limit (VARCHAR)
                                    if len(val) > max_length:
                                        # Value exceeds VARCHAR length
                                        print(f"      Warning: Value for column '{col_name}' ({len(val)} chars) exceeds VARCHAR({max_length}) limit", flush=True)
                                        print(f"      Truncating to {max_length} characters...", flush=True)
                                        truncated_val = val[:max_length]
                                        values.append(truncated_val)
                                    else:
                                        values.append(val)
                                else:
                                    # No length limit (TEXT or other types)
                                    values.append(val)
                            else:
                                values.append(val)
                
                pg_cursor.execute(
                    f'INSERT INTO "{actual_table_name}" ({column_names_str}) VALUES ({placeholders})',
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
                try:
                    pg_cursor.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
                except:
                    # If savepoint rollback fails, rollback entire transaction
                    try:
                        pg_conn.rollback()
                        # Recreate savepoint for next iteration
                        if i < total_rows:
                            savepoint_name = f"sp_row_{i+1}"
                            pg_cursor.execute(f"SAVEPOINT {savepoint_name}")
                    except:
                        pass
                
                # Show more detailed error info
                error_msg = str(e)
                print(f"  ⚠️  Error inserting row {i}: {error_msg}", flush=True)
                print(f"      Row data: {row[:3]}...", flush=True)  # Show first 3 fields
                
                # If it's an integer out of range error, show which column might be the issue
                if "integer out of range" in error_msg.lower():
                    print(f"      Hint: Check integer columns - values may exceed PostgreSQL INTEGER limits", flush=True)
                    print(f"      Consider updating table schema to use BIGINT for large integer columns", flush=True)
                continue
        
        pg_conn.commit()
        print(f"  ✓ Successfully migrated {inserted}/{len(rows)} rows", flush=True)
        return (True, inserted, total_rows_in_db)
        
    except Exception as e:
        print(f"  ❌ Error migrating table {table_name}: {e}", flush=True)
        import traceback
        traceback.print_exc()
        try:
            pg_conn.rollback()
        except:
            pass  # Connection might already be closed
        return (False, 0, total_rows_in_db if 'total_rows_in_db' in locals() else 0)

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

# Disable triggers temporarily to avoid constraint issues
try:
    pg_cursor.execute("SET session_replication_role = 'replica';")
except:
    pass  # Some PostgreSQL versions don't support this

cleared_count = 0
for pg_table in pg_tables:
    try:
        # Rollback any previous failed transaction
        try:
            pg_conn.rollback()
        except:
            pass
        
        # First try to get row count
        pg_cursor.execute(f'SELECT COUNT(*) FROM "{pg_table}"')
        count_before = pg_cursor.fetchone()[0]
        
        if count_before > 0:
            # Use TRUNCATE with CASCADE to handle foreign keys
            pg_cursor.execute(f'TRUNCATE TABLE "{pg_table}" RESTART IDENTITY CASCADE')
            pg_conn.commit()
            
            # Verify it was cleared
            pg_cursor.execute(f'SELECT COUNT(*) FROM "{pg_table}"')
            count_after = pg_cursor.fetchone()[0]
            
            cleared_count += 1
            print(f"  ✓ Cleared table: {pg_table} ({count_before} rows)", flush=True)
        else:
            cleared_count += 1
            print(f"  ✓ Table already empty: {pg_table}", flush=True)
    except Exception as e:
        # Rollback the failed transaction
        try:
            pg_conn.rollback()
        except:
            pass
        
        # If TRUNCATE fails, try DELETE
        try:
            pg_cursor.execute(f'SELECT COUNT(*) FROM "{pg_table}"')
            count_before = pg_cursor.fetchone()[0]
            
            if count_before > 0:
                pg_cursor.execute(f'DELETE FROM "{pg_table}"')
                # Reset sequence if it exists
                try:
                    pg_cursor.execute(f'ALTER SEQUENCE "{pg_table}_id_seq" RESTART WITH 1')
                except:
                    # Try alternative sequence name
                    try:
                        pg_cursor.execute(f'SELECT setval(pg_get_serial_sequence(\'"{pg_table}"\', \'id\'), 1, false)')
                    except:
                        pass  # No sequence or different name
                pg_conn.commit()
                cleared_count += 1
                print(f"  ✓ Cleared table (using DELETE): {pg_table} ({count_before} rows)", flush=True)
            else:
                cleared_count += 1
                print(f"  ✓ Table already empty: {pg_table}", flush=True)
        except Exception as e2:
            # Rollback again
            try:
                pg_conn.rollback()
            except:
                pass
            print(f"  ⚠️  Could not clear table {pg_table}: {e2}", flush=True)

# Re-enable triggers
try:
    pg_cursor.execute("SET session_replication_role = 'origin';")
except:
    pass

pg_conn.commit()
print(f"\n✓ Cleared {cleared_count}/{len(pg_tables)} PostgreSQL tables", flush=True)
print("="*70 + "\n", flush=True)

# STEP 1: Test migration with first 5 rows of each table
print("\n" + "="*70, flush=True)
print("STEP 1: TEST MIGRATION (First 5 rows of each table)", flush=True)
print("="*70, flush=True)
print("Migrating first 5 rows to verify everything works...\n", flush=True)

test_results = {}
test_success_count = 0
for table in tables:
    try:
        success, rows_migrated, total_rows = migrate_table(table, test_mode=True, limit_rows=5)
        test_results[table] = {
            'success': success,
            'rows_migrated': rows_migrated,
            'total_rows': total_rows
        }
        if success:
            test_success_count += 1
    except Exception as e:
        print(f"❌ Failed to migrate {table}: {e}", flush=True)
        test_results[table] = {
            'success': False,
            'rows_migrated': 0,
            'total_rows': 0
        }

print(f"\n{'='*70}", flush=True)
print(f"TEST MIGRATION RESULTS", flush=True)
print(f"{'='*70}", flush=True)
print(f"Successfully tested: {test_success_count}/{len(tables)} tables", flush=True)

# Check if all test migrations succeeded
all_tests_passed = all(result['success'] for result in test_results.values())

if not all_tests_passed:
    print("\n❌ Some test migrations failed. Please fix the errors above before proceeding.", flush=True)
    print("The test data has been migrated. You may need to clear it manually if you want to retry.", flush=True)
    sys.exit(1)

print("\n✓ All test migrations succeeded!", flush=True)
print("Proceeding with full migration...\n", flush=True)

# STEP 2: Clear all data (including test data) and migrate full dataset
print("\n" + "="*70, flush=True)
print("STEP 2: CLEARING ALL DATA (including test data)", flush=True)
print("="*70, flush=True)

# Clear all tables again (including the test data we just inserted)
cleared_count = 0
for pg_table in pg_tables:
    try:
        # Rollback any previous failed transaction
        try:
            pg_conn.rollback()
        except:
            pass
        
        # First try to get row count
        pg_cursor.execute(f'SELECT COUNT(*) FROM "{pg_table}"')
        count_before = pg_cursor.fetchone()[0]
        
        if count_before > 0:
            # Use TRUNCATE with CASCADE to handle foreign keys
            pg_cursor.execute(f'TRUNCATE TABLE "{pg_table}" RESTART IDENTITY CASCADE')
            pg_conn.commit()
            
            # Verify it was cleared
            pg_cursor.execute(f'SELECT COUNT(*) FROM "{pg_table}"')
            count_after = pg_cursor.fetchone()[0]
            
            cleared_count += 1
            print(f"  ✓ Cleared table: {pg_table} ({count_before} rows)", flush=True)
        else:
            cleared_count += 1
            print(f"  ✓ Table already empty: {pg_table}", flush=True)
    except Exception as e:
        # Rollback the failed transaction
        try:
            pg_conn.rollback()
        except:
            pass
        
        # If TRUNCATE fails, try DELETE
        try:
            pg_cursor.execute(f'SELECT COUNT(*) FROM "{pg_table}"')
            count_before = pg_cursor.fetchone()[0]
            
            if count_before > 0:
                pg_cursor.execute(f'DELETE FROM "{pg_table}"')
                # Reset sequence if it exists
                try:
                    pg_cursor.execute(f'ALTER SEQUENCE "{pg_table}_id_seq" RESTART WITH 1')
                except:
                    # Try alternative sequence name
                    try:
                        pg_cursor.execute(f'SELECT setval(pg_get_serial_sequence(\'"{pg_table}"\', \'id\'), 1, false)')
                    except:
                        pass  # No sequence or different name
                pg_conn.commit()
                cleared_count += 1
                print(f"  ✓ Cleared table (using DELETE): {pg_table} ({count_before} rows)", flush=True)
            else:
                cleared_count += 1
                print(f"  ✓ Table already empty: {pg_table}", flush=True)
        except Exception as e2:
            # Rollback again
            try:
                pg_conn.rollback()
            except:
                pass
            print(f"  ⚠️  Could not clear table {pg_table}: {e2}", flush=True)

print(f"\n✓ Cleared {cleared_count}/{len(pg_tables)} PostgreSQL tables", flush=True)
print("="*70 + "\n", flush=True)

# STEP 3: Full migration
print("\n" + "="*70, flush=True)
print("STEP 3: FULL MIGRATION (All data)", flush=True)
print("="*70, flush=True)
print("Migrating all data from SQLite to PostgreSQL...\n", flush=True)

success_count = 0
total_rows_migrated = 0
for table in tables:
    try:
        success, rows_migrated, total_rows = migrate_table(table, test_mode=False)
        if success:
            success_count += 1
            total_rows_migrated += rows_migrated
    except Exception as e:
        print(f"❌ Failed to migrate {table}: {e}", flush=True)

print(f"\n{'='*70}", flush=True)
print(f"MIGRATION COMPLETE", flush=True)
print(f"{'='*70}", flush=True)
print(f"Successfully migrated {success_count}/{len(tables)} tables", flush=True)
print(f"Total rows migrated: {total_rows_migrated}", flush=True)

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


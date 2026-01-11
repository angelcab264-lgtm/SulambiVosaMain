"""
Fix all PostgreSQL sequences that are out of sync
This script will reset all sequences to the correct values
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL or not DATABASE_URL.startswith('postgresql://'):
    print("⚠️  Not using PostgreSQL. This script only works with PostgreSQL.")
    sys.exit(0)

try:
    import psycopg2
    from urllib.parse import urlparse
except ImportError:
    print("❌ psycopg2 not installed. Install with: pip install psycopg2-binary")
    sys.exit(1)

print("=" * 70)
print("FIXING ALL POSTGRESQL SEQUENCES")
print("=" * 70)

try:
    result = urlparse(DATABASE_URL)
    conn = psycopg2.connect(
        database=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port or 5432
    )
    cursor = conn.cursor()
    
    # Get all tables that have SERIAL columns
    cursor.execute("""
        SELECT 
            table_name,
            column_name,
            pg_get_serial_sequence('"' || table_name || '"', column_name) as sequence_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND column_default LIKE 'nextval%'
        ORDER BY table_name, column_name;
    """)
    
    sequences_to_fix = cursor.fetchall()
    print(f"\nFound {len(sequences_to_fix)} sequences to check/fix\n")
    
    fixed_count = 0
    for table_name, column_name, sequence_name in sequences_to_fix:
        if not sequence_name:
            print(f"⚠️  Table '{table_name}' column '{column_name}': No sequence found")
            continue
        
        # Get current sequence value
        cursor.execute(f"SELECT last_value FROM {sequence_name};")
        current_value = cursor.fetchone()[0]
        
        # Get max ID from table
        # Use quoted table name for case-sensitive tables
        quoted_table = f'"{table_name}"'
        cursor.execute(f"SELECT COALESCE(MAX({column_name}), 0) FROM {quoted_table};")
        max_id = cursor.fetchone()[0]
        
        next_id = max_id + 1
        
        if current_value < next_id:
            print(f"🔧 Fixing: {sequence_name}")
            print(f"   Table: {table_name}, Column: {column_name}")
            print(f"   Current sequence value: {current_value}")
            print(f"   Max ID in table: {max_id}")
            print(f"   Setting sequence to: {next_id}")
            
            # Use setval with the sequence name directly (regclass)
            cursor.execute(f"SELECT setval(%s, %s, false);", (sequence_name, next_id))
            conn.commit()
            
            fixed_count += 1
            print(f"   ✓ Fixed!\n")
        else:
            print(f"✓ {sequence_name} is already in sync (current: {current_value}, max: {max_id})\n")
    
    conn.close()
    
    print("=" * 70)
    print(f"✓ Fixed {fixed_count} sequences")
    print("=" * 70)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


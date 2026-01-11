"""
Quick script to check if satisfaction data exists in the database
Works with both SQLite and PostgreSQL
"""

import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
DB_PATH = os.getenv("DB_PATH", "app/database/database.db")

if DATABASE_URL and DATABASE_URL.startswith('postgresql://'):
    print("Using PostgreSQL database...")
    import psycopg2
    from urllib.parse import urlparse
    
    result = urlparse(DATABASE_URL)
    conn = psycopg2.connect(
        database=result.path[1:],  # Remove leading /
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port
    )
    cursor = conn.cursor()
    
    # Check satisfactionSurveys
    cursor.execute('SELECT COUNT(*) FROM "satisfactionSurveys"')
    count = cursor.fetchone()[0]
    print(f"\n✅ satisfactionSurveys table: {count} rows")
    
    # Check semester_satisfaction
    cursor.execute('SELECT COUNT(*) FROM "semester_satisfaction"')
    count = cursor.fetchone()[0]
    print(f"✅ semester_satisfaction table: {count} rows")
    
    # Check evaluation table
    cursor.execute('SELECT COUNT(*) FROM "evaluation" WHERE "finalized" = true')
    count = cursor.fetchone()[0]
    print(f"✅ evaluation table (finalized): {count} rows")
    
    # Show some sample data
    if count > 0:
        cursor.execute('SELECT "year", "semester", "overall", "volunteers", "beneficiaries" FROM "semester_satisfaction" ORDER BY "year" DESC, "semester" DESC LIMIT 5')
        rows = cursor.fetchall()
        print(f"\n📊 Sample semester_satisfaction data (latest 5):")
        for row in rows:
            print(f"   Year {row[0]}, Semester {row[1]}: Overall={row[2]:.1f}, Vol={row[3]:.1f}, Ben={row[4]:.1f}")
    
    conn.close()
else:
    print("Using SQLite database...")
    import sqlite3
    
    if not os.path.isabs(DB_PATH):
        DB_PATH = os.path.join(os.path.dirname(__file__), DB_PATH)
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database file not found: {DB_PATH}")
        print("   Run 'python server.py --init' to create the database")
        exit(1)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='satisfactionSurveys'")
    if not cursor.fetchone():
        print("❌ satisfactionSurveys table does not exist")
        print("   Run 'python server.py --init' to create tables")
    else:
        cursor.execute("SELECT COUNT(*) FROM satisfactionSurveys")
        count = cursor.fetchone()[0]
        print(f"\n✅ satisfactionSurveys table: {count} rows")
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='semester_satisfaction'")
    if not cursor.fetchone():
        print("❌ semester_satisfaction table does not exist")
    else:
        cursor.execute("SELECT COUNT(*) FROM semester_satisfaction")
        count = cursor.fetchone()[0]
        print(f"✅ semester_satisfaction table: {count} rows")
        
        # Show some sample data
        if count > 0:
            cursor.execute("SELECT year, semester, overall, volunteers, beneficiaries FROM semester_satisfaction ORDER BY year DESC, semester DESC LIMIT 5")
            rows = cursor.fetchall()
            print(f"\n📊 Sample semester_satisfaction data (latest 5):")
            for row in rows:
                print(f"   Year {row[0]}, Semester {row[1]}: Overall={row[2]:.1f}, Vol={row[3]:.1f}, Ben={row[4]:.1f}")
    
    cursor.execute("SELECT COUNT(*) FROM evaluation WHERE finalized = 1")
    count = cursor.fetchone()[0]
    print(f"✅ evaluation table (finalized): {count} rows")
    
    conn.close()

print("\n" + "="*70)
print("💡 TIP: If tables are empty, your data might be in PostgreSQL")
print("   To test with PostgreSQL data locally, set DATABASE_URL environment variable")
print("="*70)


#!/usr/bin/env python3
"""
Check which table names the application uses vs what exists in PostgreSQL
This helps identify if there are duplicate tables or case mismatches
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
print("CHECKING TABLE NAMES: APPLICATION vs POSTGRESQL", flush=True)
print("=" * 70, flush=True)

# Table names used by the application (from Model classes)
app_table_names = {
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

# Get all tables from PostgreSQL
pg_cursor.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public'
    ORDER BY LOWER(table_name), table_name
""")
pg_tables = {row[0] for row in pg_cursor.fetchall()}

print(f"\nApplication uses {len(app_table_names)} table names", flush=True)
print(f"PostgreSQL has {len(pg_tables)} tables", flush=True)

# Check each application table
print("\n" + "=" * 70, flush=True)
print("TABLE NAME VERIFICATION", flush=True)
print("=" * 70, flush=True)

issues_found = []
for app_table in sorted(app_table_names):
    # Check exact match
    if app_table in pg_tables:
        print(f"✓ '{app_table}' - Exact match found", flush=True)
    else:
        # Check case-insensitive match
        matches = [t for t in pg_tables if t.lower() == app_table.lower()]
        if matches:
            if len(matches) > 1:
                print(f"⚠️  '{app_table}' - Multiple matches found: {matches}", flush=True)
                issues_found.append((app_table, matches, "multiple_matches"))
            else:
                print(f"⚠️  '{app_table}' - Case mismatch: Found as '{matches[0]}'", flush=True)
                issues_found.append((app_table, matches[0], "case_mismatch"))
        else:
            print(f"❌ '{app_table}' - NOT FOUND in PostgreSQL!", flush=True)
            issues_found.append((app_table, None, "not_found"))

# Check for duplicate tables (same name, different case)
print("\n" + "=" * 70, flush=True)
print("DUPLICATE TABLE DETECTION", flush=True)
print("=" * 70, flush=True)

table_names_lower = {}
for table in pg_tables:
    lower = table.lower()
    if lower not in table_names_lower:
        table_names_lower[lower] = []
    table_names_lower[lower].append(table)

duplicates = {k: v for k, v in table_names_lower.items() if len(v) > 1}
if duplicates:
    print(f"\n⚠️  Found {len(duplicates)} sets of duplicate tables (different cases):", flush=True)
    for lower_name, variants in sorted(duplicates.items()):
        print(f"  '{lower_name}': {variants}", flush=True)
        # Determine which one the app uses
        app_match = None
        for variant in variants:
            if variant in app_table_names:
                app_match = variant
                break
        if app_match:
            print(f"    → Application uses: '{app_match}'", flush=True)
            others = [v for v in variants if v != app_match]
            if others:
                print(f"    ⚠️  Consider dropping: {others}", flush=True)
        else:
            print(f"    ⚠️  None of these match application table names!", flush=True)
else:
    print("✓ No duplicate tables found", flush=True)

# Summary
print("\n" + "=" * 70, flush=True)
print("SUMMARY", flush=True)
print("=" * 70, flush=True)

if issues_found:
    print(f"\n⚠️  Found {len(issues_found)} potential issues:", flush=True)
    for app_table, match, issue_type in issues_found:
        if issue_type == "not_found":
            print(f"  - '{app_table}': Table not found in PostgreSQL", flush=True)
        elif issue_type == "case_mismatch":
            print(f"  - '{app_table}': Case mismatch (found as '{match}')", flush=True)
        elif issue_type == "multiple_matches":
            print(f"  - '{app_table}': Multiple tables found: {match}", flush=True)
else:
    print("\n✓ All application tables found with correct case!", flush=True)

if duplicates:
    print(f"\n⚠️  Found {len(duplicates)} sets of duplicate tables", flush=True)
    print("   The application will use the correctly-cased tables.", flush=True)
    print("   Consider cleaning up duplicate lowercase tables if they're empty.", flush=True)

pg_cursor.close()
pg_conn.close()

print("\n" + "=" * 70, flush=True)
print("DONE", flush=True)
print("=" * 70, flush=True)


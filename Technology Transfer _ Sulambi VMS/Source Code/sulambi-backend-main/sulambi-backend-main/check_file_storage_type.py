#!/usr/bin/env python3
"""
Check if medical certificates are stored locally or on Cloudinary
"""

import os
import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

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
    
    print("=" * 70)
    print("CHECKING MEDICAL CERTIFICATE STORAGE TYPE")
    print("=" * 70)
    
    conn = psycopg2.connect(
        database=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port or 5432,
        connect_timeout=10
    )
    cursor = conn.cursor()
    print("✓ Connected successfully!\n")
    
    # Check column names
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'requirements' 
        AND table_schema = 'public'
        AND column_name IN ('medCert', 'medcert')
        ORDER BY column_name;
    """)
    columns = [row[0] for row in cursor.fetchall()]
    medcert_col = 'medCert' if 'medCert' in columns else 'medcert'
    
    # Get all medical certificate paths
    cursor.execute(f"""
        SELECT "{medcert_col}"
        FROM "requirements"
        WHERE "{medcert_col}" IS NOT NULL 
        AND "{medcert_col}" != ''
        AND "{medcert_col}" != 'N/A'
    """)
    
    all_medcerts = cursor.fetchall()
    
    cloudinary_count = 0
    local_count = 0
    other_count = 0
    
    cloudinary_examples = []
    local_examples = []
    
    for (medcert,) in all_medcerts:
        if not medcert:
            continue
            
        medcert_str = str(medcert)
        
        # Check if it's a Cloudinary URL
        if 'cloudinary.com' in medcert_str or medcert_str.startswith('https://'):
            cloudinary_count += 1
            if len(cloudinary_examples) < 3:
                cloudinary_examples.append(medcert_str)
        # Check if it's a local path
        elif medcert_str.startswith('uploads/') or medcert_str.startswith('uploads\\'):
            local_count += 1
            if len(local_examples) < 3:
                local_examples.append(medcert_str)
        else:
            other_count += 1
    
    print("=" * 70)
    print("STORAGE TYPE BREAKDOWN")
    print("=" * 70)
    print(f"Total medical certificates: {len(all_medcerts)}")
    print(f"\n📦 Cloudinary URLs: {cloudinary_count} ({cloudinary_count/len(all_medcerts)*100:.1f}%)")
    print(f"💾 Local paths: {local_count} ({local_count/len(all_medcerts)*100:.1f}%)")
    print(f"❓ Other/Unknown: {other_count} ({other_count/len(all_medcerts)*100:.1f}%)")
    
    if cloudinary_examples:
        print("\n📦 Cloudinary Examples:")
        for i, example in enumerate(cloudinary_examples, 1):
            print(f"  {i}. {example[:80]}...")
    
    if local_examples:
        print("\n💾 Local Path Examples:")
        for i, example in enumerate(local_examples, 1):
            print(f"  {i}. {example}")
    
    # Check recent uploads (last 10)
    print("\n" + "=" * 70)
    print("RECENT UPLOADS (Last 10)")
    print("=" * 70)
    
    cursor.execute(f"""
        SELECT id, "{medcert_col}", waiver
        FROM "requirements"
        WHERE "{medcert_col}" IS NOT NULL 
        AND "{medcert_col}" != ''
        ORDER BY id DESC
        LIMIT 10
    """)
    
    recent = cursor.fetchall()
    
    recent_cloudinary = 0
    recent_local = 0
    
    for req_id, medcert, waiver in recent:
        medcert_str = str(medcert) if medcert else ""
        storage_type = "Cloudinary" if ('cloudinary.com' in medcert_str or medcert_str.startswith('https://')) else "Local"
        
        if storage_type == "Cloudinary":
            recent_cloudinary += 1
        else:
            recent_local += 1
        
        print(f"\nID: {req_id[:30]}...")
        print(f"  Medical Cert: {storage_type}")
        print(f"  Path: {medcert_str[:60]}...")
    
    print(f"\nRecent uploads breakdown:")
    print(f"  📦 Cloudinary: {recent_cloudinary}")
    print(f"  💾 Local: {recent_local}")
    
    # Check what the current upload system is configured to use
    print("\n" + "=" * 70)
    print("CURRENT UPLOAD CONFIGURATION")
    print("=" * 70)
    
    # Check if Cloudinary is configured
    cloudinary_configured = all([
        os.getenv("CLOUDINARY_CLOUD_NAME"),
        os.getenv("CLOUDINARY_API_KEY"),
        os.getenv("CLOUDINARY_API_SECRET")
    ])
    
    if cloudinary_configured:
        print("✅ Cloudinary is configured")
        print(f"   Cloud Name: {os.getenv('CLOUDINARY_CLOUD_NAME')}")
        print("   API Key: ***")
        print("   API Secret: ***")
        print("\n   Current system: Using Cloudinary for new uploads")
    else:
        print("❌ Cloudinary is NOT configured")
        print("   Missing environment variables:")
        if not os.getenv("CLOUDINARY_CLOUD_NAME"):
            print("     - CLOUDINARY_CLOUD_NAME")
        if not os.getenv("CLOUDINARY_API_KEY"):
            print("     - CLOUDINARY_API_KEY")
        if not os.getenv("CLOUDINARY_API_SECRET"):
            print("     - CLOUDINARY_API_SECRET")
        print("\n   Current system: Would use local storage (if configured)")
    
    cursor.close()
    conn.close()
    print("\n✓ Connection closed")
    print("=" * 70)
    
except ImportError:
    print("❌ ERROR: psycopg2 not installed")
    print("Install with: pip install psycopg2-binary")
    sys.exit(1)
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)





#!/usr/bin/env python3
"""
Test the getAllRequirements API endpoint to see what it actually returns
"""

import os
import sys
import json

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

# Import the requirements controller
from app.controllers.requirements import getAllRequirements

print("=" * 70)
print("TESTING getAllRequirements() API ENDPOINT")
print("=" * 70)

try:
    # Call the controller function directly
    result = getAllRequirements()
    
    if isinstance(result, tuple):
        # If it's an error tuple (message, status_code)
        print(f"❌ ERROR: {result[0]}")
        print(f"Status Code: {result[1]}")
        sys.exit(1)
    
    requirements = result.get("data", [])
    print(f"\n✅ Retrieved {len(requirements)} requirements\n")
    
    if len(requirements) == 0:
        print("⚠️  No requirements found!")
        sys.exit(0)
    
    # Check first requirement structure
    first_req = requirements[0]
    print("=" * 70)
    print("FIRST REQUIREMENT STRUCTURE")
    print("=" * 70)
    print(f"Keys: {list(first_req.keys())}")
    print(f"\nSample requirement:")
    for key, value in first_req.items():
        if key == "eventId":
            print(f"  {key}: {type(value).__name__} = {value}")
            if isinstance(value, dict):
                print(f"    Event keys: {list(value.keys()) if value else 'None'}")
                print(f"    Event title: {value.get('title') if value else 'N/A'}")
        else:
            val_str = str(value)[:60] if value else "None"
            print(f"  {key}: {val_str}")
    
    # Check for eventId issues
    print("\n" + "=" * 70)
    print("EVENT ID ANALYSIS")
    print("=" * 70)
    
    event_id_types = {}
    missing_event_title = 0
    valid_events = 0
    
    for req in requirements[:10]:  # Check first 10
        event_id = req.get("eventId")
        event_type = type(event_id).__name__
        event_id_types[event_type] = event_id_types.get(event_type, 0) + 1
        
        if isinstance(event_id, dict):
            if event_id.get("title"):
                valid_events += 1
            else:
                missing_event_title += 1
        elif isinstance(event_id, (int, str)):
            print(f"  ⚠️  Requirement {req.get('id')} has eventId as {event_type}: {event_id}")
    
    print(f"Event ID types: {event_id_types}")
    print(f"Valid events (with title): {valid_events}")
    print(f"Events missing title: {missing_event_title}")
    
    # Check accepted values
    print("\n" + "=" * 70)
    print("ACCEPTED STATUS ANALYSIS")
    print("=" * 70)
    
    accepted_types = {}
    for req in requirements:
        accepted = req.get("accepted")
        type_name = type(accepted).__name__
        accepted_types[type_name] = accepted_types.get(type_name, 0) + 1
    
    for type_name, count in accepted_types.items():
        print(f"{type_name}: {count}")
    
    # Export sample to JSON
    print("\n" + "=" * 70)
    print("EXPORTING SAMPLE TO JSON")
    print("=" * 70)
    
    sample = requirements[:3] if len(requirements) >= 3 else requirements
    with open("requirements_api_sample.json", "w", encoding="utf-8") as f:
        json.dump(sample, f, indent=2, default=str, ensure_ascii=False)
    
    print(f"✓ Exported {len(sample)} sample requirements to requirements_api_sample.json")
    
    print("\n" + "=" * 70)
    print("✅ TEST COMPLETE")
    print("=" * 70)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)





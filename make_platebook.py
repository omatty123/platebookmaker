#!/usr/bin/env python3
"""
Super Simple Platebook Generator
Usage: python3 make_platebook.py
"""

import sys
import json
import os
from platebook import generate

def main():
    print("=" * 50)
    print("📚 PLATEBOOK GENERATOR")
    print("=" * 50)
    
    # Get data source
    print("\nChoose data source:")
    print("  1. Google Sheet URL")
    print("  2. Local CSV file")
    choice = input("\nChoice [1]: ").strip() or "1"
    
    if choice == "1":
        print("\n1. Publish your Google Sheet:")
        print("   File → Share → Publish to web → CSV")
        print("\n2. Paste the published CSV URL:")
        data_source = input("\nGoogle Sheet URL: ").strip()
        
        if not data_source:
            print("❌ No URL provided. Exiting.")
            sys.exit(1)
        
        # Fetch CSV
        print("\n📥 Fetching data from Google Sheets...")
        try:
            import requests
            response = requests.get(data_source, timeout=10)
            response.raise_for_status()
            csv_text = response.text
        except Exception as e:
            print(f"❌ Error fetching sheet: {e}")
            sys.exit(1)
    
    else:
        data_source = input("\nCSV file path [hist213_lessons.csv]: ").strip()
        if not data_source:
            data_source = "hist213_lessons.csv"
        
        if not os.path.exists(data_source):
            print(f"❌ File not found: {data_source}")
            sys.exit(1)
        
        print(f"\n📥 Reading {data_source}...")
        with open(data_source, 'r') as f:
            csv_text = f.read()
    
    # Parse CSV to lessons
    print("📋 Parsing lessons...")
    lessons = []
    lines = csv_text.strip().split('\n')
    
    for line in lines[1:]:  # Skip header
        if not line.strip():
            continue
        parts = line.split(',')
        if len(parts) >= 3:
            lessons.append({
                "plate_number": int(parts[0].strip()),
                "title": parts[1].strip().replace('"', ''),
                "date": parts[2].strip().replace('"', '')
            })
    
    if not lessons:
        print("❌ No lessons found")
        sys.exit(1)
    
    print(f"✓ Found {len(lessons)} lessons")
    
    # Get course info
    print("\n📝 Course Information:")
    course = input("Course name [HIST 213 East Asia in the Modern World]: ").strip()
    if not course:
        course = "HIST 213 East Asia in the Modern World"
    
    term = input("Term [Winter 2026]: ").strip()
    if not term:
        term = "Winter 2026"
    
    output = input("Output filename [platebook.pdf]: ").strip()
    if not output:
        output = "platebook.pdf"
    
    # Create JSON for generate function
    data = {
        "course": course,
        "term": term,
        "lessons": lessons
    }
    
    # Save temp JSON
    temp_json = ".temp_lessons.json"
    with open(temp_json, 'w') as f:
        json.dump(data, f, indent=2)
    
    # Generate PDF
    print(f"\n🎨 Generating {output}...")
    try:
        generate(temp_json, output)
        print(f"\n✅ SUCCESS! Created: {output}")
        print(f"📄 Location: {os.path.abspath(output)}")
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Clean up temp file
        if os.path.exists(temp_json):
            os.remove(temp_json)

if __name__ == "__main__":
    main()

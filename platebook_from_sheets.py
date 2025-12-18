#!/usr/bin/env python3
"""
HIST 213 Platebook Generator - Google Sheets Edition
"""

import sys
import json
import argparse
import platebook  # Import the original generator

try:
    import requests
except ImportError:
    print("Missing requests. Run: pip install requests")
    sys.exit(1)

def fetch_google_sheet_csv(url):
    """Fetch CSV data from a published Google Sheet"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching Google Sheet: {e}")
        sys.exit(1)

def parse_csv_to_lessons(csv_text):
    """Parse CSV text into lessons format"""
    lessons = []
    lines = csv_text.strip().split('\n')
    
    # Skip header row
    for line in lines[1:]:
        if not line.strip():
            continue
        
        parts = line.split(',')
        if len(parts) >= 3:
            lessons.append({
                "plate_number": int(parts[0].strip()),
                "date": parts[1].strip().replace('"', ''),
                "title": parts[2].strip().replace('"', '')
            })
    
    return lessons

def main():
    parser = argparse.ArgumentParser(description='Generate platebook from Google Sheets')
    parser.add_argument('--sheet-url', help='Published Google Sheet CSV URL')
    parser.add_argument('--csv-file', help='Local CSV file path')
    parser.add_argument('--course', default='HIST 213 East Asia in the Modern World', help='Course name')
    parser.add_argument('--term', default='Winter 2026', help='Term name')
    parser.add_argument('--output', default='platebook.pdf', help='Output PDF filename')
    
    args = parser.parse_args()
    
    # Get CSV data
    if args.sheet_url:
        print(f"Fetching data from Google Sheets...")
        csv_text = fetch_google_sheet_csv(args.sheet_url)
    elif args.csv_file:
        print(f"Reading from {args.csv_file}...")
        with open(args.csv_file, 'r') as f:
            csv_text = f.read()
    else:
        print("Error: Please provide --sheet-url or --csv-file")
        sys.exit(1)
    
    # Parse lessons
    lessons = parse_csv_to_lessons(csv_text)
    print(f"Found {len(lessons)} lessons")
    
    # Create data structure
    data = {
        "course": args.course,
        "term": args.term,
        "lessons": lessons
    }
    
    # Save temp JSON
    temp_json = "_temp_lessons.json"
    with open(temp_json, 'w') as f:
        json.dump(data, f, indent=2)

    # Call the original generator
    print(f"Generating PDF: {args.output}")
    platebook.generate(temp_json, args.output)
    
    # Clean up
    import os
    if os.path.exists(temp_json):
        os.remove(temp_json)
        
    print(f"✓ Success! Created {args.output}")

if __name__ == "__main__":
    main()

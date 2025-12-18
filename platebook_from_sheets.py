#!/usr/bin/env python3
"""
HIST 213 Platebook Generator - Google Sheets Edition
Reads data from Google Sheets CSV and generates pixel-perfect PDF
"""

import json
import sys
import argparse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color, black

try:
    import requests
except ImportError:
    print("Missing requests. Run: pip install requests")
    exit(1)

# Import all constants and functions from platebook.py
exec(open('platebook.py').read())

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
    
    # Generate PDF using the existing generate function
    c = canvas.Canvas(args.output, pagesize=letter)
    
    # Cover Page
    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(BLACK)
    w = c.stringWidth(data["course"], "Helvetica-Bold", 18)
    c.drawString((PAGE_WIDTH - w) / 2, 180, data["course"])
    
    c.setFont("Helvetica-Bold", 16)
    w = c.stringWidth(data["term"], "Helvetica-Bold", 16)
    c.drawString((PAGE_WIDTH - w) / 2, 150, data["term"])
    
    c.setFont(FONT_NAME, 12)
    name = "Name:_____________________________________"
    w = c.stringWidth(name, FONT_NAME, 12)
    c.drawString((PAGE_WIDTH - w) / 2, 100, name)
    
    c.showPage()
    
    # Table of Contents
    c.setFont(FONT_NAME, 16)
    c.setFillColor(BLACK)
    title = "Table of Contents"
    w = c.stringWidth(title, FONT_NAME, 16)
    c.drawString((PAGE_WIDTH - w) / 2, PAGE_HEIGHT - 60, title)
    
    c.setLineWidth(2)
    c.line(LEFT_MARGIN, PAGE_HEIGHT - 75, RIGHT_MARGIN, PAGE_HEIGHT - 75)
    
    c.setFont(FONT_NAME, 10)
    y_pos = PAGE_HEIGHT - 100
    for lesson in data["lessons"]:
        if y_pos < 100:
            c.showPage()
            y_pos = PAGE_HEIGHT - 60
        
        plate_text = f"Plate {lesson['plate_number']}"
        c.drawString(LEFT_MARGIN, y_pos, plate_text)
        c.drawString(LEFT_MARGIN + 80, y_pos, lesson['title'])
        date_w = c.stringWidth(lesson['date'], FONT_NAME, 10)
        c.drawString(RIGHT_MARGIN - date_w, y_pos, lesson['date'])
        
        c.setDash(1, 2)
        c.setLineWidth(0.5)
        c.line(LEFT_MARGIN, y_pos - 2, RIGHT_MARGIN, y_pos - 2)
        c.setDash()
        
        y_pos -= 20
    
    c.showPage()
    
    # Generate plates
    for lesson in data["lessons"]:
        draw_standard_plate(c, lesson["plate_number"], lesson["title"], lesson["date"])
        c.showPage()
    
    c.save()
    print(f"✓ Generated: {args.output}")

if __name__ == "__main__":
    main()

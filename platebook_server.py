#!/usr/bin/env python3
"""
Platebook Local Web Server
Hosts the web interface and handles perfect PDF generation.
"""

import http.server
import socketserver
import json
import os
import sys
import shutil
import platebook_from_sheets  # Import the logic we already wrote
from platebook import generate    # The perfect generator

PORT = 8000

class PlatebookHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.path = '/platebook_generator.html'
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        if self.path == '/generate':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request = json.loads(post_data.decode('utf-8'))
            
            sheet_url = request.get('url')
            if not sheet_url:
                self.send_error(400, "Missing URL")
                return

            try:
                print(f"📥 Received request for: {sheet_url}")
                
                # Fetch and Parse
                csv_text = platebook_from_sheets.fetch_google_sheet_csv(sheet_url)
                lessons = platebook_from_sheets.parse_csv_to_lessons(csv_text)
                
                # Create Data
                data = {
                    "course": "HIST 213 East Asia in the Modern World",
                    "term": "Winter 2026",
                    "lessons": lessons
                }
                
                # Generate PDF to temp file
                output_filename = "HIST213_Platebook_Winter2026.pdf"
                temp_json = "_temp_server_lessons.json"
                
                with open(temp_json, 'w') as f:
                    json.dump(data, f, indent=2)
                
                # Generate using the PERFECT generator
                generate(temp_json, output_filename)
                
                # Clean up json
                if os.path.exists(temp_json):
                    os.remove(temp_json)

                # Send PDF back to browser
                file_size = os.path.getsize(output_filename)
                
                self.send_response(200)
                self.send_header("Content-type", "application/pdf")
                self.send_header("Content-Disposition", f"attachment; filename={output_filename}")
                self.send_header("Content-Length", file_size)
                self.end_headers()
                
                with open(output_filename, 'rb') as f:
                    shutil.copyfileobj(f, self.wfile)
                    
                print("✅ PDF sent to browser!")
                
            except Exception as e:
                print(f"❌ Error: {e}")
                self.send_error(500, str(e))
            return

print(f"🚀 Platebook Server running at http://localhost:{PORT}")
print("Press Ctrl+C to stop")

# Python 3.7+ threading
try:
    with socketserver.TCPServer(("", PORT), PlatebookHandler) as httpd:
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\nStopping server...")

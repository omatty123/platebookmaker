
import streamlit as st
import json
import requests
import os
import platebook
from platebook import generate

# Page Config
st.set_page_config(
    page_title="Platebook Generator",
    page_icon="📚",
    layout="centered"
)

# Custom CSS for a cleaner look
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        background-color: #007AFF;
        color: white;
        height: 3em;
        border-radius: 8px;
    }
    .main {
        padding-top: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.title("📚 Platebook Generator")
st.write("Generate pixel-perfect PDF platebooks from Google Sheets.")

# Input
sheet_url = st.text_input(
    "Google Sheet CSV URL",
    placeholder="https://docs.google.com/spreadsheets/d/.../pub?output=csv",
    help="File → Share → Publish to web → CSV"
)

# Advanced Options (Hidden by default)
with st.expander("Course Settings"):
    course_name = st.text_input("Course Name", value="HIST 213 East Asia in the Modern World")
    term = st.text_input("Term", value="Winter 2026")

def fetch_and_parse_csv(url):
    response = requests.get(url)
    response.raise_for_status()
    csv_text = response.text
    
    lessons = []
    lines = csv_text.strip().split('\n')
    # Skip header
    for line in lines[1:]:
        if not line.strip(): continue
        parts = line.split(',')
        if len(parts) >= 3:
            lessons.append({
                "plate_number": int(parts[0].strip()),
                "date": parts[1].strip().replace('"', ''),
                "title": parts[2].strip().replace('"', '')
            })
    return lessons

# Generate Button
if st.button("Generate Platebook"):
    if not sheet_url:
        st.error("Please enter a Google Sheet URL")
    else:
        try:
            with st.spinner("Fetching data and generating PDF..."):
                # Fetch Data
                lessons = fetch_and_parse_csv(sheet_url)
                
                # Prepare JSON for generator
                data = {
                    "course": course_name,
                    "term": term,
                    "lessons": lessons
                }
                
                temp_json = "_temp_streamlit.json"
                output_pdf = "platebook.pdf"
                
                with open(temp_json, 'w') as f:
                    json.dump(data, f)
                
                # Generate PDF
                platebook.generate(temp_json, output_pdf)
                
                # Success & Download
                st.success(f"✓ Generated {len(lessons)} plates successfully!")
                
                with open(output_pdf, "rb") as pdf_file:
                    st.download_button(
                        label="⬇️ Download PDF",
                        data=pdf_file,
                        file_name="HIST213_Platebook.pdf",
                        mime="application/pdf"
                    )
                
                # Cleanup
                if os.path.exists(temp_json):
                    os.remove(temp_json)

        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.write("Make sure your link is a **Published to Web CSV** link.")

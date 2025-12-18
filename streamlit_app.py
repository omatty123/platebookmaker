
import streamlit as st
import json
import requests
import os
import re
import pandas as pd
import platebook
from platebook import generate

# Page Config
st.set_page_config(
    page_title="Platebook Generator",
    page_icon="📚",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        background-color: #007AFF;
        color: white;
        height: 3em;
        border-radius: 8px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #0056b3;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.title("📚 Platebook Generator")
st.markdown("Turn your **Syllabus** directly into a **Pixel-Perfect PDF**.")

# Tabs for input methods
tab1, tab2 = st.tabs(["📝 Paste Syllabus (Magic)", "🔗 Google Sheet URL"])

with tab1:
    st.subheader("1. Paste Syllabus Text")
    syllabus_text = st.text_area(
        "Paste your class schedule here (dates and titles)",
        height=300,
        placeholder="Jan 6\nIntroduction to the class\n\nJan 8\nEast Asian Language..."
    )

    if syllabus_text:
        st.subheader("2. Verify & Edit Lessons")
        
        # --- PARSING LOGIC ---
        # Look for patterns like "Jan 6", "Feb 12", "March 3" followed by text
        # This is a simple parser; can be improved
        lines = syllabus_text.split('\n')
        parsed_data = []
        
        current_date = None
        current_title_parts = []
        
        # Regex for extraction (Month Day)
        date_pattern = re.compile(r'^(Jan|Feb|Mar|March|Apr|April|May|Jun|June|Aug|Sept|Sep|Oct|Nov|Dec)\s+\d{1,2}.*')
        
        plate_count = 1
        
        for line in lines:
            line = line.strip()
            if not line: continue
            
            # Is it a date?
            if date_pattern.match(line):
                # Save previous lesson if exists
                if current_date and current_title_parts:
                    title = " ".join(current_title_parts).strip()
                    # Basic filtering for holidays/midterms
                    if "No Class" not in title and "Midterm" not in title:
                        parsed_data.append({
                            "Plate": plate_count,
                            "Date": current_date,
                            "Title": title
                        })
                        plate_count += 1
                
                # Start new lesson
                # Split date from rest of line if on same line
                match = date_pattern.match(line)
                # Heuristic: assume date is valid, rest is title part 1
                # Often syllabus lines are "Jan 6 Topic"
                # We need to split properly.
                
                # Let's clean the date strictly
                # Just take the first few words as date?
                # A safer bet: User verifies anyway.
                current_date = line # Store whole line first, user edits
                current_title_parts = [] 
            else:
                if current_date:
                    current_title_parts.append(line)
        
        # Add last one
        if current_date and current_title_parts:
             title = " ".join(current_title_parts).strip()
             if "No Class" not in title and "Midterm" not in title:
                parsed_data.append({
                    "Plate": plate_count,
                    "Date": current_date,
                    "Title": title
                })

        # Create DataFrame
        if parsed_data:
            df = pd.DataFrame(parsed_data)
        else:
            # Fallback empty
            df = pd.DataFrame(columns=["Plate", "Date", "Title"])

        # DATA EDITOR
        edited_df = st.data_editor(
            df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Plate": st.column_config.NumberColumn("Plate #", step=1),
                "Date": st.column_config.TextColumn("Date"),
                "Title": st.column_config.TextColumn("Lesson Title"),
            }
        )

        st.info(f"Ready to generate **{len(edited_df)} plates**.")
        
        if st.button("✨ Generate PDF from Syllabus", key="btn_syllabus"):
            if edited_df.empty:
                st.error("No lessons to generate!")
            else:
                try:
                    with st.spinner("Generating perfect PDF..."):
                        # Convert DF to list of dicts
                        lessons = []
                        for _, row in edited_df.iterrows():
                            lessons.append({
                                "plate_number": int(row["Plate"]),
                                "date": str(row["Date"]),
                                "title": str(row["Title"])
                            })
                        
                        # Set default course info
                        data = {
                            "course": "HIST 213 East Asia in the Modern World",
                            "term": "Winter 2026",
                            "lessons": lessons
                        }
                        
                        # File paths
                        temp_json = "_temp_stream_syl.json"
                        output_pdf = "platebook.pdf"
                        
                        with open(temp_json, 'w') as f:
                            json.dump(data, f)
                            
                        # Generate
                        platebook.generate(temp_json, output_pdf)
                        
                        # Download
                        with open(output_pdf, "rb") as pdf_file:
                            st.download_button(
                                label="⬇️ Download PDF Platebook",
                                data=pdf_file,
                                file_name="Syllabus_Platebook.pdf",
                                mime="application/pdf"
                            )
                        
                        # Cleanup
                        if os.path.exists(temp_json): os.remove(temp_json)
                        st.balloons()
                        
                except Exception as e:
                    st.error(f"Error: {e}")


with tab2:
    st.subheader("Import from Google Sheet")
    sheet_url = st.text_input(
        "Google Sheet CSV URL",
        placeholder="https://docs.google.com/spreadsheets/d/.../pub?output=csv"
    )

    if st.button("Generate from Sheet", key="btn_sheet"):
        if not sheet_url:
            st.error("Please enter a URL")
        else:
            try:
                # Fetch
                response = requests.get(sheet_url)
                response.raise_for_status()
                csv_text = response.text
                
                # Parse
                lessons = []
                for line in csv_text.strip().split('\n')[1:]:
                    if not line.strip(): continue
                    p = line.split(',')
                    if len(p) >= 3:
                        lessons.append({
                            "plate_number": int(p[0].strip()),
                            "date": p[1].strip().replace('"', ''),
                            "title": p[2].strip().replace('"', '')
                        })
                
                # Generate
                data = {
                    "course": "HIST 213 East Asia in the Modern World",
                    "term": "Winter 2026",
                    "lessons": lessons
                }
                
                temp_json = "_temp_sheet.json"
                output_pdf = "platebook_sheet.pdf"
                
                with open(temp_json, 'w') as f: json.dump(data, f)
                platebook.generate(temp_json, output_pdf)
                
                st.success("Generated!")
                with open(output_pdf, "rb") as pdf_file:
                    st.download_button(
                        label="⬇️ Download PDF",
                        data=pdf_file,
                        file_name="GoogleSheet_Platebook.pdf",
                        mime="application/pdf"
                    )
                if os.path.exists(temp_json): os.remove(temp_json)

            except Exception as e:
                st.error(f"Error: {e}")

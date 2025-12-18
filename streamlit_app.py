
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

# Sidebar
with st.sidebar:
    st.header("🎨 Design Settings")
    
    # Cover Image
    st.subheader("Cover Image")
    cover_image = st.file_uploader("Upload Image (Optional)", type=['png', 'jpg', 'jpeg'])
    
    st.divider()
    
    # Course Info
    st.subheader("Course Details")
    course_name = st.text_input("Course Name", value="HIST 213 East Asia in the Modern World")
    term_name = st.text_input("Term", value="Winter 2026")

# Header
st.title("📚 Platebook Generator")
st.markdown("Turn your **Syllabus** directly into a **Pixel-Perfect PDF**.")

# Tabs
tab1, tab2 = st.tabs(["📝 Paste Syllabus (Magic)", "🔗 Google Sheet URL"])

# Helper to save image
def save_uploaded_image(uploaded_file):
    if uploaded_file is not None:
        temp_path = "temp_cover_image.png"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return temp_path
    return None

# --- TAB 1: SYLLABUS PARSER ---
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
        lines = syllabus_text.split('\n')
        parsed_data = []
        current_date = None
        current_title_parts = []
        date_pattern = re.compile(r'^(Jan|Feb|Mar|March|Apr|April|May|Jun|June|Aug|Sept|Sep|Oct|Nov|Dec)\s+\d{1,2}.*')
        plate_count = 1
        
        for line in lines:
            line = line.strip()
            if not line: continue
            
            if date_pattern.match(line):
                if current_date and current_title_parts:
                    title = " ".join(current_title_parts).strip()
                    if "No Class" not in title and "Midterm" not in title:
                        parsed_data.append({"Plate": plate_count, "Date": current_date, "Title": title})
                        plate_count += 1
                current_date = line
                current_title_parts = [] 
            else:
                if current_date: current_title_parts.append(line)
        
        if current_date and current_title_parts:
             title = " ".join(current_title_parts).strip()
             if "No Class" not in title and "Midterm" not in title:
                parsed_data.append({"Plate": plate_count, "Date": current_date, "Title": title})

        # Data Editor
        df = pd.DataFrame(parsed_data) if parsed_data else pd.DataFrame(columns=["Plate", "Date", "Title"])
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
                        lessons = []
                        for _, row in edited_df.iterrows():
                            lessons.append({
                                "plate_number": int(row["Plate"]),
                                "date": str(row["Date"]),
                                "title": str(row["Title"])
                            })
                        
                        data = {"course": course_name, "term": term_name, "lessons": lessons}
                        temp_json = "_temp_stream_syl.json"
                        output_pdf = "platebook.pdf"
                        
                        # Save Image
                        img_path = save_uploaded_image(cover_image)
                        
                        # Generate
                        with open(temp_json, 'w') as f: json.dump(data, f)
                        platebook.generate(temp_json, output_pdf, cover_image_path=img_path)
                        
                        # Download using read()
                        with open(output_pdf, "rb") as f:
                            pdf_data = f.read()
                            
                        st.download_button(
                            label="⬇️ Download PDF Platebook",
                            data=pdf_data,
                            file_name="Syllabus_Platebook.pdf",
                            mime="application/pdf"
                        )
                        
                        # Cleanup
                        if os.path.exists(temp_json): os.remove(temp_json)
                        if img_path and os.path.exists(img_path): os.remove(img_path)
                        st.balloons()
                        
                except Exception as e:
                    st.error(f"Error: {e}")

# --- TAB 2: GOOGLE SHEET ---
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
                with st.spinner("Fetching and generating..."):
                    response = requests.get(sheet_url)
                    response.raise_for_status()
                    csv_text = response.text
                    
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
                    
                    data = {"course": course_name, "term": term_name, "lessons": lessons}
                    temp_json = "_temp_sheet.json"
                    output_pdf = "platebook_sheet.pdf"
                    
                    # Save Image
                    img_path = save_uploaded_image(cover_image)
                    
                    # Generate
                    with open(temp_json, 'w') as f: json.dump(data, f)
                    platebook.generate(temp_json, output_pdf, cover_image_path=img_path)
                    
                    # Download using read()
                    with open(output_pdf, "rb") as f:
                        pdf_data = f.read()
                        
                    st.download_button(
                        label="⬇️ Download PDF",
                        data=pdf_data,
                        file_name="GoogleSheet_Platebook.pdf",
                        mime="application/pdf"
                    )
                    
                    if os.path.exists(temp_json): os.remove(temp_json)
                    if img_path and os.path.exists(img_path): os.remove(img_path)

            except Exception as e:
                st.error(f"Error: {e}")

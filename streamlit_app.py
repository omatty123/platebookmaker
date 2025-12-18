
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
        current_date_str = None
        current_title_parts = []
        plate_count = 1
        
        # State for smart parsing
        current_month = None
        current_year = "2026" # Default from your syllabus, or current year
        
        # Regex patterns
        # 1. "1/5" or "1 / 5"
        slash_date = re.compile(r'^(\d{1,2})\s*/\s*(\d{1,2})')
        # 2. "Jan 6"
        text_date = re.compile(r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+(\d{1,2})', re.IGNORECASE)
        # 3. Just a number "7" (only if we have a current month)
        bare_day = re.compile(r'^(\d{1,2})$')

        # Helper to format date
        def format_date(m, d):
            start_m = int(m) if str(m).isdigit() else 1
            # Simple mapping if text
            months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            if str(m).isalpha(): 
                # try to find index
                for i, mon in enumerate(months):
                    if mon.lower() in m.lower():
                        return f"{mon} {d}"
                return f"{m} {d}"
            
            if 1 <= start_m <= 12:
                return f"{months[start_m-1]} {d}"
            return f"{m}/{d}"

        # Helper to clean title noise
        def clean_line_text(text):
            # Remove "ANTHOLOGY:" prefix
            text = re.sub(r'^ANTHOLOGY:\s*', '', text, flags=re.IGNORECASE)
            # Remove page numbers like (pp 3-24) or (30-48) or (123 - 456)
            text = re.sub(r'\(\s*\d+\s*[-–]\s*\d+\s*\)', '', text)
            text = re.sub(r'\(pp?\.?\s*\d+.*?\)', '', text, flags=re.IGNORECASE)
            
            # Remove "Introduction and Translation by..."
            text = re.sub(r'Introduction and Translation.*', '', text, flags=re.IGNORECASE)
            
            # Remove assignments/papers
            text = re.sub(r'PAPER #\d+.*', '', text, flags=re.IGNORECASE)
            text = re.sub(r'Final paper.*', '', text, flags=re.IGNORECASE)
            text = re.sub(r'Paper #\d+.*', '', text, flags=re.IGNORECASE)
            text = re.sub(r'Preliminary Thesis.*', '', text, flags=re.IGNORECASE)
            text = re.sub(r'.*Due.*', '', text, flags=re.IGNORECASE)
            
            # Remove "Turn in..." or "Submit..." if they appear (just in case)
            text = re.sub(r'Turn in.*', '', text, flags=re.IGNORECASE)
            
            # Remove file extensions or urls
            text = re.sub(r'https?://\S+', '', text)
            text = re.sub(r'\[.*?\]\s*\(https.*?\)', '', text) # markdown links
            
            return text.strip(" ,.-:")

        for line in lines:
            line = line.strip()
            if not line: continue
            
            is_new_date = False
            new_date_val = None
            remainder = ""

            # Check 1: Slash Date (1/5)
            m_slash = slash_date.match(line)
            if m_slash:
                m, d = m_slash.groups()
                current_month = m
                new_date_val = format_date(m, d)
                remainder = line[m_slash.end():].strip()
                is_new_date = True
            
            # Check 2: Text Date (Jan 6)
            elif text_date.match(line):
                m_text = text_date.match(line)
                m, d = m_text.groups()
                current_month = m
                new_date_val = format_date(m, d)
                remainder = line[m_text.end():].strip()
                is_new_date = True

            # Check 3: Bare Day (7)
            elif current_month:
                m_bare = re.match(r'^(\d{1,2})\s+(.*)', line)
                m_bare_solo = re.match(r'^(\d{1,2})$', line)
                
                if m_bare:
                    d = m_bare.group(1)
                    if int(d) <= 31: 
                        new_date_val = format_date(current_month, d)
                        remainder = m_bare.group(2).strip()
                        is_new_date = True
                elif m_bare_solo:
                    d = m_bare_solo.group(1)
                    if int(d) <= 31:
                         new_date_val = format_date(current_month, d)
                         remainder = ""
                         is_new_date = True

            # PROCESS MATCH
            if is_new_date:
                # Save previous lesson
                if current_date_str:
                    # Join all parts
                    cleaned_parts = [clean_line_text(p) for p in current_title_parts]
                    cleaned_parts = [p for p in cleaned_parts if p] # Remove empty
                    final_title = " / ".join(cleaned_parts)
                    
                    if final_title and "No Class" not in final_title and "Midterm" not in final_title and "MTRP" not in final_title:
                        parsed_data.append({"Plate": plate_count, "Date": current_date_str, "Title": final_title})
                        plate_count += 1
                        
                current_date_str = new_date_val
                current_title_parts = [remainder] if remainder else []
            else:
                # Not a date -> content line for current lesson
                if current_date_str:
                    if "WEEK" not in line and "Page" not in line:
                         current_title_parts.append(line)
        
        # Add last one
        if current_date_str:
             cleaned_parts = [clean_line_text(p) for p in current_title_parts]
             cleaned_parts = [p for p in cleaned_parts if p]
             final_title = " / ".join(cleaned_parts)
             
             if final_title and "No Class" not in final_title and "Midterm" not in final_title and "MTRP" not in final_title:
                parsed_data.append({"Plate": plate_count, "Date": current_date_str, "Title": final_title})

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

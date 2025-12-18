
import streamlit as st
import json
import requests
import os
import re
import pandas as pd
import base64
import platebook
from platebook import generate

# Page Config
st.set_page_config(
    page_title="Platebook Generator",
    page_icon="📚",
    layout="wide"
)

# Custom CSS for Premium Look
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }
    
    /* MONTAFON MOONLIGHT THEME */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
        color: #111827; /* Gray 900 */
        background-color: #ffffff;
    }
    
    /* The Moonlight Glow - Vignette */
    .stApp {
        background: radial-gradient(circle at 50% 0%, rgba(37, 99, 235, 0.08) 0%, transparent 60%),
                    #ffffff;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #111827 !important;
        font-weight: 600 !important;
        letter-spacing: -0.02em;
    }
    
    /* Hero Section - Card Style */
    .hero {
        background-color: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(229, 231, 235, 0.5);
        padding: 2.5rem;
        border-radius: 12px;
        color: #111827;
        margin-bottom: 2rem;
        text-align: left;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
    }
    .hero h1 {
        font-size: 2.5rem !important;
        font-weight: 700;
        margin-bottom: 0.5rem;
        color: #2563eb !important; /* Electric Blue Accent */
    }
    .hero p {
        font-size: 1.125rem;
        color: #4b5563; /* Gray 600 */
        font-weight: 400;
        margin: 0;
    }

    /* Tabs - Clean & Spaced */
    .stTabs [data-baseweb="tab-list"] {
        gap: 16px;
        border-bottom: 1px solid #e5e7eb;
        padding-bottom: 0;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 6px 6px 0 0;
        padding: 10px 20px;
        border: none;
        color: #6b7280; /* Gray 500 */
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: transparent !important;
        color: #2563eb !important; /* Electric Blue */
        border-bottom: 2px solid #2563eb;
        font-weight: 600;
    }

    /* Button - Electric Blue */
    div.stButton > button {
        background-color: #2563eb; /* Electric Blue */
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px; /* 12px might be too round for small button */
        font-weight: 500;
        width: 100%;
        transition: all 0.2s ease;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
    }
    div.stButton > button:hover {
        background-color: #1d4ed8; /* Darker Blue */
        transform: translateY(-1px);
        box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2);
    }
    
    /* Inputs - refined */
    .stTextArea textarea, .stTextInput input {
        border-radius: 8px;
        border: 1px solid #d1d5db; /* Gray 300 */
        padding: 0.75rem;
        transition: border-color 0.15s ease;
    }
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #2563eb; /* Electric Blue */
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1); /* Glow ring */
    }
    </style>
""", unsafe_allow_html=True)

# Hero Header (Moonlight)
st.markdown("""
<div class="hero">
    <h1>Platebook Generator</h1>
    <p>Professional Syllabus Typesetting. <b>Pixel-Perfect.</b></p>
</div>
""", unsafe_allow_html=True)

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

# Helper to parse header info
def parse_header_info(text):
    lines = text.split('\n')
    c_name = None
    t_name = None
    
    # scan first few lines
    for i, line in enumerate(lines[:15]): # Scan a bit deeper
        line = line.strip()
        if not line: continue
        
        # Ignore Google Doc/System junk
        if line.startswith("[") or line.startswith("http") or "Report abuse" in line:
            continue
        
        # Term Regex (Winter 2026, Fall 2025, etc)
        term_match = re.search(r'(Fall|Winter|Spring|Summer)\s+\d{4}', line, re.IGNORECASE)
        if term_match: t_name = term_match.group(0)
        
        # Course Name: First substantial line that ISN'T the term
        if not c_name and len(line) > 5 and not term_match:
            # If line is "Syllabus" or similar, skip
            if "syllabus" in line.lower() and len(line) < 15: continue
            c_name = line
            
    return c_name, t_name

# Initialize defaults
if 'course_name_input' not in st.session_state:
    st.session_state.course_name_input = ""
if 'term_name_input' not in st.session_state:
    st.session_state.term_name_input = ""

# --- TAB 1: SYLLABUS PARSER (Render First to capture input) ---
with tab1:
    st.subheader("1. ✨ Paste Syllabus Text")
    syllabus_text = st.text_area(
        "Simply Copy & Paste your entire syllabus below. We'll handle the rest.",
        height=300,
        placeholder="Course Name: Chinese Literature\nTerm: Winter 2026\n\nJan 6\nIntroduction to the class\n(pp 1-10)\n\nJan 8\nBook of Songs...\n\n(We will automatically extract the course name, term, and clear lesson cleaning rules!)"
    )

    # Auto-detect header info immediately after input
    if syllabus_text:
        detected_course, detected_term = parse_header_info(syllabus_text)
        # Update state if fields are empty
        if detected_course and not st.session_state.course_name_input:
             st.session_state.course_name_input = detected_course
        if detected_term and not st.session_state.term_name_input:
             st.session_state.term_name_input = detected_term

    # --- NOW RENDER SIDEBAR (After state potentially updated) ---
    # --- NOW RENDER SIDEBAR (After state potentially updated) ---
    with st.sidebar:
        st.header("⚙️ Cover & Settings")
        
        st.caption("Upload a custom cover image to make your platebook stand out.")
        cover_image = st.file_uploader("Upload Cover Image", type=['png', 'jpg', 'jpeg'])
        
        st.divider()
        
        st.subheader("📚 Course Details")
        st.caption("Auto-filled from your syllabus, or edit manually.")
        
        # identifying key allows bidirectional sync
        course_name = st.text_input("Course Name", key="course_name_input", placeholder="e.g. Chinese Literature")
        term_name = st.text_input("Term", key="term_name_input", placeholder="e.g. Winter 2026")
        
        st.divider()
        st.info("💡 **Pro Tip**: Paste your syllabus to auto-fill these fields!")

    # --- CONTINUE TAB 1 LOGIC ---
    if syllabus_text:
        st.subheader("2. ✅ Verify & Edit Lessons")
        # ... parsing logic continues ...
        
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

        # Helper to clean title noise (Make it SHORT and COGENT)
        def clean_line_text(text):
            # Remove "ANTHOLOGY:" prefix
            text = re.sub(r'^ANTHOLOGY:\s*', '', text, flags=re.IGNORECASE)
            
            # Remove parentheses entirely (usually page numbers, dates, translators)
            # e.g. (pp 3-24), (190-210), (Available as...)
            text = re.sub(r'\s*\(.*?\)', '', text)
            
            # Remove "Dynasty" prefixes
            text = re.sub(r'\b\w+\s+Dynasty\b', '', text, flags=re.IGNORECASE)
            
            # Remove quotes
            text = text.replace('“', '').replace('”', '').replace('"', '')
            
            # Remove "pp." if it appears outside parens
            text = re.sub(r'pp\.?\s*\d+[-–]\d+', '', text, flags=re.IGNORECASE)
            
            # Remove "Vol." or "New York" (Bibliographic info)
            text = re.sub(r'Vol\.?\s*\d+', '', text, flags=re.IGNORECASE)
            text = re.sub(r'New York:.*', '', text, flags=re.IGNORECASE)
            
            # Remove common Author names (Specific to this syllabus but useful generally)
            text = re.sub(r'\b(Ivanhoe|Van Norden|Birch|Turner|Slingerland|Kjellberg|Hutton|Harris)\b.*', '', text, flags=re.IGNORECASE)
            
            # Remove "Introduction" if it's generic (followed by comma or colon)
            text = re.sub(r'^Introduction\s*[,:]\s*', '', text, flags=re.IGNORECASE)
            text = re.sub(r'Introduction and Translation.*', '', text, flags=re.IGNORECASE)
            
            # Remove assignments/papers
            text = re.sub(r'PAPER #\d+.*', '', text, flags=re.IGNORECASE)
            text = re.sub(r'Final paper.*', '', text, flags=re.IGNORECASE)
            text = re.sub(r'Preliminary Thesis.*', '', text, flags=re.IGNORECASE)
            text = re.sub(r'.*Due.*', '', text, flags=re.IGNORECASE)
            
            # Remove file extensions or urls markdown
            text = re.sub(r'\[.*?\]\s*\(https.*?\)', '', text) 
            
            # Remove "Week X" if it ended up in the title
            text = re.sub(r'Week\s+\d+', '', text, flags=re.IGNORECASE)
            
            # Remove "Listen to..."
            text = re.sub(r'Listen to.*', '', text, flags=re.IGNORECASE)
            
            # Remove "Blast from the past"
            text = re.sub(r'Blast from the past.*', '', text, flags=re.IGNORECASE)
            
            # Remove "Story of..." (Miss Li, Tsui Ying-Ying, etc)
            text = re.sub(r'Story of.*', '', text, flags=re.IGNORECASE)
            text = re.sub(r'The Story of.*', '', text, flags=re.IGNORECASE)
            text = re.sub(r'Funny story.*', '', text, flags=re.IGNORECASE)
            
            # Remove "Selections from..."
            text = re.sub(r'Selections from.*', '', text, flags=re.IGNORECASE)
            
            # Remove Su Shi notes
            text = re.sub(r'.*Su Shi.*', '', text, flags=re.IGNORECASE)
            text = re.sub(r'.*Dongpo.*', '', text, flags=re.IGNORECASE)
            
            # Clean up extra spaces
            text = re.sub(r'\s+', ' ', text).strip()
            return text.strip(" ,.-:/") # added slash to strip

        for line in lines:
            line = line.strip()
            if not line: continue
            
            # Skip "Final Presentation" lines entirely
            if "final presentation" in line.lower(): continue
            
            is_new_date = False
            new_date_val = None
            remainder = ""

            # Check 1: Slash Date (1/5)
            # ... (regex logic same as before) ...
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
                    
                    # Deduplicate? No, sequence matters.
                    # Smart Assembly: Fit whole parts into 120 chars
                    final_title = ""
                    for i, part in enumerate(cleaned_parts):
                        if i == 0:
                            final_title = part
                        else:
                            # Check if adding this part keeps us under 120
                            if len(final_title) + 3 + len(part) <= 120:
                                final_title += " / " + part
                            else:
                                # Start of a new part would limit us?
                                # If we have space for at least 15 chars, maybe truncate the part?
                                # User said "Make the tough decision". 
                                # Decision: Drop subsequent parts if they don't fit.
                                break 
                    
                    if final_title and "No Class" not in final_title and "Midterm" not in final_title and "MTRP" not in final_title and "Final presentation" not in final_title.lower():
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
             # Smart Assembly: Fit whole parts into 120 chars
             final_title = ""
             for i, part in enumerate(cleaned_parts):
                 if i == 0:
                     final_title = part
                 else:
                     if len(final_title) + 3 + len(part) <= 120:
                         final_title += " / " + part
                     else:
                         break
             
             if final_title and "No Class" not in final_title and "Midterm" not in final_title and "MTRP" not in final_title and "Final presentation" not in final_title.lower():
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
                        
                        st.balloons()
                        
                        # Preview PDF
                        st.markdown("### 📄 PDF Preview")
                        base64_pdf = base64.b64encode(pdf_data).decode('utf-8')
                        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
                        st.markdown(pdf_display, unsafe_allow_html=True)
                        
                        # Fallback link
                        st.markdown(f'<a href="data:application/pdf;base64,{base64_pdf}" download="Syllabus_Platebook.pdf">Open Preview in New Tab</a>', unsafe_allow_html=True)
                        
                        # Cleanup
                        if os.path.exists(temp_json): os.remove(temp_json)
                        if img_path and os.path.exists(img_path): os.remove(img_path)
                        
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
                    
                    # Preview PDF
                    st.markdown("### 📄 PDF Preview")
                    base64_pdf = base64.b64encode(pdf_data).decode('utf-8')
                    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
                    st.markdown(pdf_display, unsafe_allow_html=True)
                    
                    # Fallback link
                    st.markdown(f'<a href="data:application/pdf;base64,{base64_pdf}" download="GoogleSheet_Platebook.pdf">Open Preview in New Tab</a>', unsafe_allow_html=True)
                    
                    if os.path.exists(temp_json): os.remove(temp_json)
                    if img_path and os.path.exists(img_path): os.remove(img_path)

            except Exception as e:
                st.error(f"Error: {e}")

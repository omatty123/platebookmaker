"""
HIST 213 Platebook Template Generator
====================================

Authoritative generator for HIST 213 platebooks.
Layout is reverse-engineered from HIST213_Platebook_Winter2026.pdf
and MUST NOT be changed without re-measuring the PDF.

Usage:
    python platebook.py lessons.json output.pdf
"""

import json
import sys
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color, black

# =============================================================================
# PAGE + DESIGN CONSTANTS  (DO NOT CHANGE)
# =============================================================================

PAGE_WIDTH, PAGE_HEIGHT = letter

LEFT_MARGIN = 36
RIGHT_MARGIN = 576
TOP_MARGIN = 29

LIGHT_GRAY = Color(0.96, 0.96, 0.96)  # Lighter, more subtle gray
WHITE = Color(1, 1, 1)
BLACK = black
GRID_GRAY = Color(0.88, 0.88, 0.88)  # For grid lines

CORNER_RADIUS = 8  # Slightly more rounded for elegant look
HEADER_CORNER_RADIUS = 1  # Barely rounded headers - crisp and professional
FONT_NAME = "Times-Roman"  # Serif font for academic style
FONT_SIZE = 11

# -----------------------------------------------------------------------------
# Layout (measured from top of page)
# -----------------------------------------------------------------------------

HEADER_Y = 29
HEADER_HEIGHT = 28

PLATE_NUM_X = 36
PLATE_NUM_WIDTH = 85

TITLE_X = 125
TITLE_WIDTH = 280

DATE_X = 465
DATE_WIDTH = 111

PPT_LABEL_Y = 68
PPT_LABEL_HEIGHT = 24

PERSON_LABEL_X = 36
PERSON_LABEL_WIDTH = 65

PLACE_LABEL_X = 216
PLACE_LABEL_WIDTH = 55

THING_LABEL_X = 396
THING_LABEL_WIDTH = 60

PPT_CONTENT_START_Y = 92
PPT_CONTENT_HEIGHT = 20  # Reduced from 40 to 20 (half size)
PPT_CONTENT_WIDTH = 180
PPT_ROWS = 3

TIMELINE_LABEL_Y = 158  # Shifted up from 218 (60 points saved from PPT)
TIMELINE_LABEL_HEIGHT = 24
TIMELINE_LABEL_WIDTH = 70

TIMELINE_BOX_Y = 182  # Shifted up from 242
TIMELINE_BOX_HEIGHT = 60
TIMELINE_BOX_WIDTH = 540

TIMELINE_LINE_Y = 212  # Shifted up from 272
TICK_START_X = 50
TICK_END_X = 562
TICK_COUNT = 11

MAP_LABEL_Y = 248  # Shifted up from 308
MAP_LABEL_HEIGHT = 24
MAP_LABEL_WIDTH = 45

MAP_BOX_Y = 272  # Shifted up from 332
MAP_BOX_HEIGHT = 200  # Increased from 160 to 200 (using extra space from PPT reduction)
MAP_BOX_WIDTH = 540

PQ_LABEL_Y = 483  # Shifted down from 443 (40 points for bigger map)
PQ_LABEL_HEIGHT = 24
PQ_LABEL_WIDTH = 165

VSA_LABEL_X = 410
VSA_LABEL_WIDTH = 166

Q_ROW_START_Y = 507  # Shifted down from 467
Q_ROW_HEIGHT = 50
Q_NUM_WIDTH = 30
Q_CONTENT_WIDTH = 330
Q_ANSWER_WIDTH = 180

CEC_LABEL_Y = 622  # Shifted down from 582
CEC_LABEL_HEIGHT = 20
CEC_LABEL_WIDTH = 185

NOTES_LABEL_X = 312
NOTES_LABEL_WIDTH = 55

BOTTOM_BOX_Y = 642  # Shifted down from 602
BOTTOM_BOX_HEIGHT = 88
BOTTOM_LEFT_WIDTH = 264
BOTTOM_RIGHT_WIDTH = 264
BOTTOM_RIGHT_X = 312

# =============================================================================
# DRAWING HELPERS
# =============================================================================

def _y(top, height):
    return PAGE_HEIGHT - top - height

def draw_grid_background(c, x, top, w, h, grid_size=10):
    """Draw subtle grid pattern background"""
    y = _y(top, h)

    # Draw grid lines
    c.setStrokeColor(GRID_GRAY)
    c.setLineWidth(0.3)

    # Vertical lines
    for i in range(0, int(w) + 1, grid_size):
        c.line(x + i, y, x + i, y + h)

    # Horizontal lines
    for i in range(0, int(h) + 1, grid_size):
        c.line(x, y + i, x + w, y + i)

def draw_square(c, x, top, w, h, fill=False, gray=False):
    """Draw square-cornered box for content areas"""
    y = _y(top, h)
    c.setLineWidth(1.0)
    c.setStrokeColor(BLACK)

    if fill:
        if gray:
            c.setFillColor(LIGHT_GRAY)
        else:
            c.setFillColor(WHITE)
        c.rect(x, y, w, h, stroke=1, fill=1)
    else:
        c.rect(x, y, w, h, stroke=1, fill=0)

def draw_grid_box(c, x, top, w, h):
    """Draw square box with only grid background (no ruled lines)"""
    y = _y(top, h)

    # Draw grid background
    draw_grid_background(c, x, top, w, h)

    # Draw outer border
    c.setLineWidth(1.0)
    c.setStrokeColor(BLACK)
    c.rect(x, y, w, h, stroke=1, fill=0)

def draw_lined_box(c, x, top, w, h, line_spacing=12):
    """Draw square box with grid background and horizontal ruled lines for writing"""
    y = _y(top, h)

    # Draw grid background first (like timeline)
    draw_grid_background(c, x, top, w, h)

    # Draw outer border
    c.setLineWidth(1.0)
    c.setStrokeColor(BLACK)
    c.rect(x, y, w, h, stroke=1, fill=0)

    # Draw horizontal ruled lines (darker than grid)
    c.setStrokeColor(Color(0.75, 0.75, 0.75))  # Darker gray for writing lines
    c.setLineWidth(0.5)
    num_lines = int(h / line_spacing)
    for i in range(1, num_lines):
        line_y = y + (i * line_spacing)
        c.line(x, line_y, x + w, line_y)

    # Reset stroke color
    c.setStrokeColor(BLACK)

def draw_round(c, x, top, w, h, fill=False, gray=False, grid=False, radius=None):
    if radius is None:
        radius = CORNER_RADIUS

    y = _y(top, h)
    c.setLineWidth(1.0)  # Slightly thicker borders for visibility
    c.setStrokeColor(BLACK)

    if grid:
        # Draw grid background first
        draw_grid_background(c, x, top, w, h)
        # Then draw border
        c.setLineWidth(1.0)
        c.setStrokeColor(BLACK)
        c.roundRect(x, y, w, h, radius, stroke=1, fill=0)
    elif fill:
        if gray:
            c.setFillColor(LIGHT_GRAY)
        else:
            c.setFillColor(WHITE)
        c.roundRect(x, y, w, h, radius, stroke=1, fill=1)
    else:
        c.roundRect(x, y, w, h, radius, stroke=1, fill=0)


def draw_centered(c, text, x, top, w, h, size=FONT_SIZE, bold=False):
    font = "Times-Bold" if bold else FONT_NAME
    
    # Auto-shrink logic
    current_size = size
    min_size = 6
    text_width = c.stringWidth(text, font, current_size)
    available_width = w - 4 # 2px padding on each side
    
    while text_width > available_width and current_size > min_size:
        current_size -= 0.5
        text_width = c.stringWidth(text, font, current_size)
    
    c.setFont(font, current_size)
    c.setFillColor(BLACK)  # Ensure text is always black
    y = _y(top, h) + (h - current_size) / 2 + 2 # Recenter vertically based on new size
    c.drawString(x + (w - text_width) / 2, y, text)

# =============================================================================
# PLATE DRAWING (NO PAGINATION HERE)
# =============================================================================

def draw_standard_plate(c, n, title, date):
    # Header - less rounded corners, bigger text
    draw_round(c, PLATE_NUM_X, HEADER_Y, PLATE_NUM_WIDTH, HEADER_HEIGHT, radius=HEADER_CORNER_RADIUS)
    draw_centered(c, f"Plate # {n}", PLATE_NUM_X, HEADER_Y, PLATE_NUM_WIDTH, HEADER_HEIGHT, size=14, bold=True)

    # Calculate dynamic date box width
    date_text_width = c.stringWidth(date, "Times-Bold", 14)
    date_box_width = date_text_width + 20  # Add padding
    date_box_x = RIGHT_MARGIN - date_box_width

    # Title extends to just before date box
    title_box_width = date_box_x - TITLE_X - 10
    draw_round(c, TITLE_X, HEADER_Y, title_box_width, HEADER_HEIGHT, radius=HEADER_CORNER_RADIUS)
    draw_centered(c, title, TITLE_X, HEADER_Y, title_box_width, HEADER_HEIGHT, size=13, bold=True)

    draw_round(c, date_box_x, HEADER_Y, date_box_width, HEADER_HEIGHT, radius=HEADER_CORNER_RADIUS)
    draw_centered(c, date, date_box_x, HEADER_Y, date_box_width, HEADER_HEIGHT, size=14, bold=True)

    # Person / Place / Thing labels - 10pt bold to fit
    draw_round(c, PERSON_LABEL_X, PPT_LABEL_Y, PERSON_LABEL_WIDTH, PPT_LABEL_HEIGHT)
    draw_centered(c, "Person", PERSON_LABEL_X, PPT_LABEL_Y, PERSON_LABEL_WIDTH, PPT_LABEL_HEIGHT, size=10, bold=True)

    draw_round(c, PLACE_LABEL_X, PPT_LABEL_Y, PLACE_LABEL_WIDTH, PPT_LABEL_HEIGHT)
    draw_centered(c, "Place", PLACE_LABEL_X, PPT_LABEL_Y, PLACE_LABEL_WIDTH, PPT_LABEL_HEIGHT, size=10, bold=True)

    draw_round(c, THING_LABEL_X, PPT_LABEL_Y, THING_LABEL_WIDTH, PPT_LABEL_HEIGHT)
    draw_centered(c, "Thing", THING_LABEL_X, PPT_LABEL_Y, THING_LABEL_WIDTH, PPT_LABEL_HEIGHT, size=10, bold=True)

    # 3×3 grid - grid background only (no ruled lines for short entries)
    for row in range(PPT_ROWS):
        y = PPT_CONTENT_START_Y + row * PPT_CONTENT_HEIGHT
        for x in (36, 216, 396):
            draw_grid_box(c, x, y, PPT_CONTENT_WIDTH, PPT_CONTENT_HEIGHT)

    # Timeline - 10pt bold to fit
    draw_round(c, LEFT_MARGIN, TIMELINE_LABEL_Y, TIMELINE_LABEL_WIDTH, TIMELINE_LABEL_HEIGHT)
    draw_centered(c, "Timeline", LEFT_MARGIN, TIMELINE_LABEL_Y,
                  TIMELINE_LABEL_WIDTH, TIMELINE_LABEL_HEIGHT, size=10, bold=True)

    draw_round(c, LEFT_MARGIN, TIMELINE_BOX_Y, TIMELINE_BOX_WIDTH, TIMELINE_BOX_HEIGHT, grid=True)

    y = PAGE_HEIGHT - TIMELINE_LINE_Y
    c.line(TICK_START_X, y, TICK_END_X, y)
    step = (TICK_END_X - TICK_START_X) / TICK_COUNT
    for i in range(TICK_COUNT + 1):
        x = TICK_START_X + i * step
        c.line(x, y - 8, x, y + 8)

    # Map - 10pt bold to fit
    draw_round(c, LEFT_MARGIN, MAP_LABEL_Y, MAP_LABEL_WIDTH, MAP_LABEL_HEIGHT)
    draw_centered(c, "Map", LEFT_MARGIN, MAP_LABEL_Y,
                  MAP_LABEL_WIDTH, MAP_LABEL_HEIGHT, size=10, bold=True)
    draw_grid_box(c, LEFT_MARGIN, MAP_BOX_Y, MAP_BOX_WIDTH, MAP_BOX_HEIGHT)  # Grid background for map

    # Questions - larger font for readability
    draw_round(c, LEFT_MARGIN, PQ_LABEL_Y, PQ_LABEL_WIDTH, PQ_LABEL_HEIGHT)
    draw_centered(c, "Penetrating Questions", LEFT_MARGIN, PQ_LABEL_Y,
                  PQ_LABEL_WIDTH, PQ_LABEL_HEIGHT, size=11, bold=True)

    draw_round(c, VSA_LABEL_X, PQ_LABEL_Y, VSA_LABEL_WIDTH, PQ_LABEL_HEIGHT)
    draw_centered(c, "Very short answers", VSA_LABEL_X, PQ_LABEL_Y,
                  VSA_LABEL_WIDTH, PQ_LABEL_HEIGHT, size=11, bold=True)

    for i in range(2):
        y = Q_ROW_START_Y + i * 60
        draw_round(c, LEFT_MARGIN, y, Q_NUM_WIDTH, Q_ROW_HEIGHT)
        draw_centered(c, str(i + 1), LEFT_MARGIN, y, Q_NUM_WIDTH, Q_ROW_HEIGHT, size=10, bold=True)
        draw_lined_box(c, LEFT_MARGIN + Q_NUM_WIDTH, y, Q_CONTENT_WIDTH, Q_ROW_HEIGHT, line_spacing=10)
        draw_lined_box(c, 396, y, Q_ANSWER_WIDTH, Q_ROW_HEIGHT, line_spacing=10)

    # Bottom - larger font for readability
    draw_round(c, LEFT_MARGIN, CEC_LABEL_Y, CEC_LABEL_WIDTH, CEC_LABEL_HEIGHT)
    draw_centered(c, "Causes / Effects / Connections",
                  LEFT_MARGIN, CEC_LABEL_Y, CEC_LABEL_WIDTH, CEC_LABEL_HEIGHT, size=11, bold=True)

    draw_round(c, NOTES_LABEL_X, CEC_LABEL_Y, NOTES_LABEL_WIDTH, CEC_LABEL_HEIGHT)
    draw_centered(c, "Notes",
                  NOTES_LABEL_X, CEC_LABEL_Y, NOTES_LABEL_WIDTH, CEC_LABEL_HEIGHT, size=10, bold=True)

    draw_grid_box(c, LEFT_MARGIN, BOTTOM_BOX_Y, BOTTOM_LEFT_WIDTH, BOTTOM_BOX_HEIGHT)  # Grid only, no lines
    draw_lined_box(c, BOTTOM_RIGHT_X, BOTTOM_BOX_Y, BOTTOM_RIGHT_WIDTH, BOTTOM_BOX_HEIGHT, line_spacing=10)

def draw_presentation_plate(c, n, date):
    draw_round(c, PLATE_NUM_X, HEADER_Y, PLATE_NUM_WIDTH, HEADER_HEIGHT, radius=HEADER_CORNER_RADIUS)
    draw_centered(c, f"Plate # {n}", PLATE_NUM_X, HEADER_Y, PLATE_NUM_WIDTH, HEADER_HEIGHT, size=14, bold=True)

    # Calculate dynamic date box width
    date_text_width = c.stringWidth(date, "Times-Bold", 14)
    date_box_width = date_text_width + 20  # Add padding
    date_box_x = RIGHT_MARGIN - date_box_width

    # Title extends to just before date box
    title_box_width = date_box_x - TITLE_X - 10
    draw_round(c, TITLE_X, HEADER_Y, title_box_width, HEADER_HEIGHT, radius=HEADER_CORNER_RADIUS)
    draw_centered(c, "Final presentations", TITLE_X, HEADER_Y, title_box_width, HEADER_HEIGHT, size=13, bold=True)

    draw_round(c, date_box_x, HEADER_Y, date_box_width, HEADER_HEIGHT, radius=HEADER_CORNER_RADIUS)
    draw_centered(c, date, date_box_x, HEADER_Y, date_box_width, HEADER_HEIGHT, size=14, bold=True)

    draw_round(c, LEFT_MARGIN, 78, 55, 24)
    draw_centered(c, "Notes", LEFT_MARGIN, 78, 55, 24, bold=True)

    draw_lined_box(c, LEFT_MARGIN, 102, 540, 618, line_spacing=14)

# =============================================================================
# MAIN
# =============================================================================

def generate(lessons_file, output_pdf, cover_image_path=None):
    with open(lessons_file) as f:
        data = json.load(f)

    c = canvas.Canvas(output_pdf, pagesize=letter)

    # Cover Page - title at bottom, large space for image at top
    # Draw image if provided
    if cover_image_path:
        try:
            # Draw image centered in the top space
            # Available space: approx y=250 to y=750
            img_width = 500
            img_height = 400
            c.drawImage(cover_image_path, (PAGE_WIDTH - img_width)/2, 280, 
                       width=img_width, height=img_height, 
                       preserveAspectRatio=True, anchor='c')
        except Exception as e:
            print(f"Error drawing cover image: {e}")

    c.setFont("Times-Bold", 18)
    c.setFillColor(BLACK)
    w = c.stringWidth(data["course"], "Times-Bold", 18)
    c.drawString((PAGE_WIDTH - w) / 2, 180, data["course"])

    c.setFont("Times-Bold", 16)
    w = c.stringWidth(data["term"], "Times-Bold", 16)
    c.drawString((PAGE_WIDTH - w) / 2, 150, data["term"])

    c.setFont(FONT_NAME, 12)
    name = "Name:_____________________________________"
    w = c.stringWidth(name, FONT_NAME, 12)
    c.drawString((PAGE_WIDTH - w) / 2, 100, name)

    c.showPage()

    # Table of Contents (Page 2) - Attractive design
    c.setFont("Times-Bold", 20)
    c.setFillColor(BLACK)
    title = "Table of Contents"
    w = c.stringWidth(title, "Times-Bold", 20)
    c.drawString((PAGE_WIDTH - w) / 2, PAGE_HEIGHT - 50, title)

    # Elegant double line under title
    c.setLineWidth(2)
    c.line(LEFT_MARGIN, PAGE_HEIGHT - 70, RIGHT_MARGIN, PAGE_HEIGHT - 70)
    c.setLineWidth(0.5)
    c.line(LEFT_MARGIN, PAGE_HEIGHT - 74, RIGHT_MARGIN, PAGE_HEIGHT - 74)
    
    # TOC Helper
    def truncate_text(c, text, font, size, max_width):
        if c.stringWidth(text, font, size) <= max_width:
            return text
        while c.stringWidth(text + "...", font, size) > max_width and len(text) > 0:
            text = text[:-1]
        return text + "..."

    c.setFont("Times-Bold", 11)
    y_pos = PAGE_HEIGHT - 95
    toc_left = 80  # More compact left margin
    toc_right = PAGE_WIDTH - 80  # More compact right margin

    for lesson in data["lessons"]:
        if y_pos < 100:  # Start new page if needed
            c.showPage()
            y_pos = PAGE_HEIGHT - 60

        # Plate number in bold
        plate_text = f"Plate {lesson['plate_number']}"
        c.drawString(toc_left, y_pos, plate_text)

        # Title in regular Times
        c.setFont(FONT_NAME, 11)
        date_w = c.stringWidth(lesson['date'], FONT_NAME, 11)
        max_title_w = (toc_right - date_w - 15) - (toc_left + 70)

        short_title = truncate_text(c, lesson['title'], FONT_NAME, 11, max_title_w)
        c.drawString(toc_left + 70, y_pos, short_title)

        # Date in bold
        c.setFont("Times-Bold", 11)
        c.drawString(toc_right - date_w, y_pos, lesson['date'])

        # Light separator line
        c.setStrokeColor(Color(0.85, 0.85, 0.85))
        c.setLineWidth(0.5)
        c.line(toc_left, y_pos - 4, toc_right, y_pos - 4)
        c.setStrokeColor(BLACK)

        c.setFont("Times-Bold", 11)  # Reset for next plate number
        y_pos -= 22

    c.showPage()

    for lesson in data["lessons"]:
        if lesson.get("presentation"):
            draw_presentation_plate(c, lesson["plate_number"], lesson["date"])
        else:
            draw_standard_plate(c,
                                lesson["plate_number"],
                                lesson["title"],
                                lesson["date"])
        c.showPage()

    c.save()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python platebook.py lessons.json output.pdf")
        sys.exit(1)

    generate(sys.argv[1], sys.argv[2])

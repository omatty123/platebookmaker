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

LIGHT_GRAY = Color(0.933333, 0.933333, 0.933333)
WHITE = Color(1, 1, 1)
BLACK = black

CORNER_RADIUS = 5
FONT_NAME = "Helvetica"
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

def draw_round(c, x, top, w, h, fill=False, gray=False):
    y = _y(top, h)
    c.setLineWidth(0.5)
    c.setStrokeColor(BLACK)
    if fill:
        if gray:
            c.setFillColor(LIGHT_GRAY)
        else:
            c.setFillColor(WHITE)
        c.roundRect(x, y, w, h, CORNER_RADIUS, stroke=1, fill=1)
    else:
        c.roundRect(x, y, w, h, CORNER_RADIUS, stroke=1, fill=0)


def draw_centered(c, text, x, top, w, h, size=FONT_SIZE, bold=False):
    font = "Helvetica-Bold" if bold else FONT_NAME
    c.setFont(font, size)
    c.setFillColor(BLACK)  # Ensure text is always black
    tw = c.stringWidth(text, font, size)
    y = _y(top, h) + (h - size) / 2 + 2
    c.drawString(x + (w - tw) / 2, y, text)

# =============================================================================
# PLATE DRAWING (NO PAGINATION HERE)
# =============================================================================

def draw_standard_plate(c, n, title, date):
    # Header - 12pt bold to fit in boxes
    draw_round(c, PLATE_NUM_X, HEADER_Y, PLATE_NUM_WIDTH, HEADER_HEIGHT)
    draw_centered(c, f"Plate # {n}", PLATE_NUM_X, HEADER_Y, PLATE_NUM_WIDTH, HEADER_HEIGHT, size=12, bold=True)

    draw_round(c, TITLE_X, HEADER_Y, TITLE_WIDTH, HEADER_HEIGHT)
    draw_centered(c, title, TITLE_X, HEADER_Y, TITLE_WIDTH, HEADER_HEIGHT, size=11, bold=True)

    draw_round(c, DATE_X, HEADER_Y, DATE_WIDTH, HEADER_HEIGHT)
    draw_centered(c, date, DATE_X, HEADER_Y, DATE_WIDTH, HEADER_HEIGHT, size=12, bold=True)

    # Person / Place / Thing labels - 10pt bold to fit
    draw_round(c, PERSON_LABEL_X, PPT_LABEL_Y, PERSON_LABEL_WIDTH, PPT_LABEL_HEIGHT)
    draw_centered(c, "Person", PERSON_LABEL_X, PPT_LABEL_Y, PERSON_LABEL_WIDTH, PPT_LABEL_HEIGHT, size=10, bold=True)

    draw_round(c, PLACE_LABEL_X, PPT_LABEL_Y, PLACE_LABEL_WIDTH, PPT_LABEL_HEIGHT)
    draw_centered(c, "Place", PLACE_LABEL_X, PPT_LABEL_Y, PLACE_LABEL_WIDTH, PPT_LABEL_HEIGHT, size=10, bold=True)

    draw_round(c, THING_LABEL_X, PPT_LABEL_Y, THING_LABEL_WIDTH, PPT_LABEL_HEIGHT)
    draw_centered(c, "Thing", THING_LABEL_X, PPT_LABEL_Y, THING_LABEL_WIDTH, PPT_LABEL_HEIGHT, size=10, bold=True)

    # 3×3 grid - gray fill for content boxes
    for row in range(PPT_ROWS):
        y = PPT_CONTENT_START_Y + row * PPT_CONTENT_HEIGHT
        for x in (36, 216, 396):
            draw_round(c, x, y, PPT_CONTENT_WIDTH, PPT_CONTENT_HEIGHT, fill=True, gray=True)

    # Timeline - 10pt bold to fit
    draw_round(c, LEFT_MARGIN, TIMELINE_LABEL_Y, TIMELINE_LABEL_WIDTH, TIMELINE_LABEL_HEIGHT)
    draw_centered(c, "Timeline", LEFT_MARGIN, TIMELINE_LABEL_Y,
                  TIMELINE_LABEL_WIDTH, TIMELINE_LABEL_HEIGHT, size=10, bold=True)

    draw_round(c, LEFT_MARGIN, TIMELINE_BOX_Y, TIMELINE_BOX_WIDTH, TIMELINE_BOX_HEIGHT, fill=True, gray=True)

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
    draw_round(c, LEFT_MARGIN, MAP_BOX_Y, MAP_BOX_WIDTH, MAP_BOX_HEIGHT, fill=True, gray=True)

    # Questions - 9pt bold to fit long labels
    draw_round(c, LEFT_MARGIN, PQ_LABEL_Y, PQ_LABEL_WIDTH, PQ_LABEL_HEIGHT)
    draw_centered(c, "Penetrating Questions", LEFT_MARGIN, PQ_LABEL_Y,
                  PQ_LABEL_WIDTH, PQ_LABEL_HEIGHT, size=9, bold=True)

    draw_round(c, VSA_LABEL_X, PQ_LABEL_Y, VSA_LABEL_WIDTH, PQ_LABEL_HEIGHT)
    draw_centered(c, "Very short answers", VSA_LABEL_X, PQ_LABEL_Y,
                  VSA_LABEL_WIDTH, PQ_LABEL_HEIGHT, size=9, bold=True)

    for i in range(2):
        y = Q_ROW_START_Y + i * 60
        draw_round(c, LEFT_MARGIN, y, Q_NUM_WIDTH, Q_ROW_HEIGHT)
        draw_centered(c, str(i + 1), LEFT_MARGIN, y, Q_NUM_WIDTH, Q_ROW_HEIGHT, size=10, bold=True)
        draw_round(c, LEFT_MARGIN + Q_NUM_WIDTH, y, Q_CONTENT_WIDTH, Q_ROW_HEIGHT, fill=True, gray=True)
        draw_round(c, 396, y, Q_ANSWER_WIDTH, Q_ROW_HEIGHT, fill=True, gray=True)

    # Bottom - 8pt bold to fit long labels
    draw_round(c, LEFT_MARGIN, CEC_LABEL_Y, CEC_LABEL_WIDTH, CEC_LABEL_HEIGHT)
    draw_centered(c, "Causes / Effects / Connections",
                  LEFT_MARGIN, CEC_LABEL_Y, CEC_LABEL_WIDTH, CEC_LABEL_HEIGHT, size=8, bold=True)

    draw_round(c, NOTES_LABEL_X, CEC_LABEL_Y, NOTES_LABEL_WIDTH, CEC_LABEL_HEIGHT)
    draw_centered(c, "Notes",
                  NOTES_LABEL_X, CEC_LABEL_Y, NOTES_LABEL_WIDTH, CEC_LABEL_HEIGHT, size=10, bold=True)

    draw_round(c, LEFT_MARGIN, BOTTOM_BOX_Y, BOTTOM_LEFT_WIDTH, BOTTOM_BOX_HEIGHT, fill=True, gray=True)
    draw_round(c, BOTTOM_RIGHT_X, BOTTOM_BOX_Y, BOTTOM_RIGHT_WIDTH, BOTTOM_BOX_HEIGHT, fill=True, gray=True)

def draw_presentation_plate(c, n, date):
    draw_round(c, PLATE_NUM_X, HEADER_Y, PLATE_NUM_WIDTH, HEADER_HEIGHT)
    draw_centered(c, f"Plate # {n}", PLATE_NUM_X, HEADER_Y, PLATE_NUM_WIDTH, HEADER_HEIGHT)

    draw_round(c, TITLE_X, HEADER_Y, 153, HEADER_HEIGHT)
    draw_centered(c, "Final presentations", TITLE_X, HEADER_Y, 153, HEADER_HEIGHT)

    draw_round(c, DATE_X, HEADER_Y, DATE_WIDTH, HEADER_HEIGHT)
    draw_centered(c, date, DATE_X, HEADER_Y, DATE_WIDTH, HEADER_HEIGHT)

    draw_round(c, LEFT_MARGIN, 78, 55, 24)
    draw_centered(c, "Notes", LEFT_MARGIN, 78, 55, 24)

    draw_round(c, LEFT_MARGIN, 102, 540, 618, fill=True)

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

    # Table of Contents (Page 2)
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
        if y_pos < 100:  # Start new page if needed
            c.showPage()
            y_pos = PAGE_HEIGHT - 60
        
        plate_text = f"Plate {lesson['plate_number']}"
        c.drawString(LEFT_MARGIN, y_pos, plate_text)
        c.drawString(LEFT_MARGIN + 80, y_pos, lesson['title'])
        date_w = c.stringWidth(lesson['date'], FONT_NAME, 10)
        c.drawString(RIGHT_MARGIN - date_w, y_pos, lesson['date'])
        
        # Dotted line
        c.setDash(1, 2)
        c.setLineWidth(0.5)
        c.line(LEFT_MARGIN, y_pos - 2, RIGHT_MARGIN, y_pos - 2)
        c.setDash()
        
        y_pos -= 20

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

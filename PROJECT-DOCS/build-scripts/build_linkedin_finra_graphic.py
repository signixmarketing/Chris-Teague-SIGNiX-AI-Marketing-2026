#!/usr/bin/env python3
"""
Build SIGNiX LinkedIn pull quote graphic — RIA / FINRA compliance post.

Visual style matches the credit union pull quote format with one change:
the left accent bar is RED (#dc2626) instead of green to signal risk/warning.

Output:
  PROJECT-DOCS/DELIVERABLES/SIGNiX-LinkedIn-PullQuote-FINRA-April2026.png
"""

import os
from PIL import Image, ImageDraw, ImageFont

# Brand tokens
INK   = (46,  52,  64)
RED   = (220,  38,  38)
GREEN = (109, 163,  74)
WHITE = (255, 255, 255)

W, H = 1200, 628

HELVETICA = "/System/Library/Fonts/Helvetica.ttc"

def load(path, size, index=0):
    try:
        return ImageFont.truetype(path, size, index=index)
    except Exception:
        return ImageFont.load_default()

font_quote     = load(HELVETICA, 68, index=1)
font_quote_sm  = load(HELVETICA, 56, index=1)
font_attr      = load(HELVETICA, 28, index=1)
font_logo      = load(HELVETICA, 42, index=1)
font_openquote = load(HELVETICA, 110, index=1)

OUTPUT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "DELIVERABLES",
    "SIGNiX-LinkedIn-PullQuote-FINRA-April2026.png"
)

img  = Image.new("RGB", (W, H), INK)
draw = ImageDraw.Draw(img)

# Red left accent bar (risk signal)
draw.rectangle([(0, 0), (14, H)], fill=RED)

# Open-quote mark in red
draw.text((60, 22), "\u201C", font=font_openquote, fill=RED)

# Line 1
LINE1 = "It was not a software failure."
# Line 2
LINE2 = "The supervision failed."

draw.text((60, 168), LINE1, font=font_quote,    fill=WHITE)
draw.text((60, 252), LINE2, font=font_quote_sm, fill=WHITE)

# Attribution in red
draw.text((60, 336), "FINRA enforcement pattern, 2022-2025", font=font_attr, fill=RED)

# SIGNiX wordmark bottom right
sign_bbox = draw.textbbox((0, 0), "SIGN", font=font_logo)
ix_bbox   = draw.textbbox((0, 0), "iX",   font=font_logo)
sign_w = sign_bbox[2] - sign_bbox[0]
logo_x = W - (sign_w + (ix_bbox[2] - ix_bbox[0])) - 52
logo_y = H - 70
draw.text((logo_x,          logo_y), "SIGN", font=font_logo, fill=WHITE)
draw.text((logo_x + sign_w, logo_y), "iX",   font=font_logo, fill=GREEN)

img.save(OUTPUT, "PNG", dpi=(300, 300))
print(f"  Written: {OUTPUT}")

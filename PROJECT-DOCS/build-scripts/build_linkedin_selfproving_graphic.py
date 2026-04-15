#!/usr/bin/env python3
"""
Build SIGNiX LinkedIn pull quote graphic — Self-Proving Signatures post.

Matches the visual style of SIGNiX-LinkedIn-PullQuote-CreditUnion-April2026.png:
  - 1200x628 dark INK background
  - Green left accent bar
  - Large white bold quote text
  - Green attribution line
  - SIGNiX wordmark bottom right

Output:
  PROJECT-DOCS/DELIVERABLES/SIGNiX-LinkedIn-PullQuote-SelfProving-April2026.png
"""

import os
from PIL import Image, ImageDraw, ImageFont

# ── Brand tokens ──────────────────────────────────────────────────────────────
INK        = (46,  52,  64)    # #2e3440
GREEN      = (109, 163, 74)    # #6da34a
WHITE      = (255, 255, 255)
WHITE_DIM  = (220, 225, 232)

# ── Canvas ────────────────────────────────────────────────────────────────────
W, H = 1200, 628

# ── Fonts ─────────────────────────────────────────────────────────────────────
HELVETICA = "/System/Library/Fonts/Helvetica.ttc"
SFNS      = "/System/Library/Fonts/SFNS.ttf"

def load(path, size, index=0):
    try:
        return ImageFont.truetype(path, size, index=index)
    except Exception:
        return ImageFont.load_default()

font_quote      = load(HELVETICA, 72, index=1)   # Helvetica Bold — main quote
font_quote_sm   = load(HELVETICA, 72, index=1)   # line 2
font_attr       = load(HELVETICA, 30, index=1)   # attribution line
font_logo_main  = load(HELVETICA, 42, index=1)   # SIGN
font_logo_ix    = load(HELVETICA, 42, index=1)   # iX
font_openquote  = load(HELVETICA, 120, index=1)  # large "

# ── Output path ───────────────────────────────────────────────────────────────
OUTPUT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "DELIVERABLES",
    "SIGNiX-LinkedIn-PullQuote-SelfProving-April2026.png"
)

# ── Draw ──────────────────────────────────────────────────────────────────────
img  = Image.new("RGB", (W, H), INK)
draw = ImageDraw.Draw(img)

# Left accent bar
BAR_W = 14
draw.rectangle([(0, 0), (BAR_W, H)], fill=GREEN)

# Open-quote mark
QUOTE_X = 60
QUOTE_Y = 28
draw.text((QUOTE_X, QUOTE_Y), "\u201C", font=font_openquote, fill=GREEN)

# Main quote text — two lines
LINE1 = "Your signature proves itself."
LINE2 = "No platform required."

TEXT_X  = 60
LINE1_Y = 185
LINE2_Y = LINE1_Y + 92

draw.text((TEXT_X, LINE1_Y), LINE1, font=font_quote,    fill=WHITE)
draw.text((TEXT_X, LINE2_Y), LINE2, font=font_quote_sm, fill=WHITE)

# Attribution
ATTR_Y = LINE2_Y + 100
draw.text((TEXT_X, ATTR_Y), "Self-proving digital signatures", font=font_attr, fill=GREEN)

# SIGNiX wordmark — bottom right
# Measure widths to position correctly
sign_bbox = draw.textbbox((0, 0), "SIGN", font=font_logo_main)
ix_bbox   = draw.textbbox((0, 0), "iX",   font=font_logo_ix)
sign_w = sign_bbox[2] - sign_bbox[0]
ix_w   = ix_bbox[2]   - ix_bbox[0]
logo_w = sign_w + ix_w
logo_x = W - logo_w - 52
logo_y = H - 70
draw.text((logo_x,          logo_y), "SIGN", font=font_logo_main, fill=WHITE)
draw.text((logo_x + sign_w, logo_y), "iX",   font=font_logo_ix,   fill=GREEN)

# ── Save ──────────────────────────────────────────────────────────────────────
img.save(OUTPUT, "PNG", dpi=(300, 300))
print(f"  Written: {OUTPUT}")

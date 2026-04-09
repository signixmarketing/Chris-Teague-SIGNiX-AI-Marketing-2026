# SIGNiX Document Build Scripts

Python scripts for generating branded Word and PowerPoint documents. Run these any time you need a new `.docx` or `.pptx` from a SIGNiX content outline.

**Last updated:** 2026-04-02

---

## Requirements

Both scripts use Python 3 and two libraries. Install once:

```bash
pip3 install python-docx python-pptx
```

---

## Scripts

### `build_signix_docx.py`

Builds a branded `.docx` Word document.

**What it produces:** `SIGNIX-PAID-MEDIA-PLAN-2026.docx`

**To run:**
```bash
python3 "PROJECT-DOCS/build-scripts/build_signix_docx.py"
```

**To reuse for a new document:**
1. Duplicate the file and rename it (e.g. `build_signix_onepager.py`)
2. Keep all the helper functions at the top unchanged
3. Replace the content section (below `# ── BUILD`) with your new document structure
4. Update the output path at the bottom

---

### `build_signix_pptx.py`

Builds a branded `.pptx` PowerPoint presentation.

**What it produces:** `SIGNIX-PAID-MEDIA-SLIDES.pptx`

**To run:**
```bash
python3 "PROJECT-DOCS/build-scripts/build_signix_pptx.py"
```

**To reuse for a new deck:**
1. Duplicate the file and rename it (e.g. `build_signix_new_deck.py`)
2. Keep all the helper functions at the top unchanged (`rect`, `txb`, `bullet_card`, `top_bar`, `header`, `footer`, etc.)
3. Replace each slide section with your new content
4. Update the output path at the bottom

---

## SIGNiX brand tokens (used in both scripts)

| Token | Hex | Usage |
|---|---|---|
| `GREEN` | `#6da34a` | CTAs, accents, eyebrow labels, tag pills |
| `INK` | `#2e3440` | Headlines, bold text, dark card backgrounds |
| `BODY` | `#545454` | Paragraph text |
| `MUTED` | `#6b7280` | Meta text, footnotes |
| `WHITE` | `#ffffff` | Text on dark backgrounds |
| `CANVAS` | `#f8fafb` | Light card / panel backgrounds |
| `RULE` | `#d8dee9` | Dividers and separators |

Full design reference: `PROJECT-DOCS/DESIGN-GUIDELINES.md`

---

## Key helper functions (pptx)

| Function | What it does |
|---|---|
| `rect(slide, l, t, w, h, color)` | Draws a solid rectangle shape |
| `txb(slide, l, t, w, h, text, ...)` | Adds a single-style text box |
| `mixed_txb(slide, ..., segments)` | Adds a text box with bold+normal mixed runs |
| `bullet_card(slide, ..., header, items)` | Draws a branded card with header + bullet list |
| `top_bar(slide)` | Adds the green 5px top accent bar |
| `header(slide, eyebrow, title)` | Adds the eyebrow label + slide title |
| `footer(slide)` | Adds the footer rule + SIGNiX logo mark |

## Key helper functions (docx)

| Function | What it does |
|---|---|
| `add_h1(doc, text)` | Title heading — 24pt bold ink |
| `add_h2(doc, text)` | Section heading — 16pt bold ink with green bottom rule |
| `add_h3(doc, text)` | Sub-heading — 12pt bold green |
| `add_body(doc, text)` | Body paragraph with inline **bold** markdown support |
| `add_bullet(doc, text)` | Bullet list item with inline **bold** support |
| `add_table(doc, headers, rows, col_widths)` | Branded table — dark ink headers, alternating rows |
| `add_blockquote(doc, text)` | Indented italic quote with green left border |
| `add_hr(doc)` | Horizontal rule in muted gray |

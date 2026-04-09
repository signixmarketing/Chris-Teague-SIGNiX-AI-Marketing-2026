# SIGNiX simple fold-over greeting card (5×7) — VistaPrint

**Plain branded card:** outside only shows the **SIGNiX logo** (full-color wordmark on the **back**, reverse wordmark on the **dark front cover**). **Inside is blank** so reps can write their own message.

Print specs match the Mike email kit colors (`#6da34a`, `#2e3440`, `#f8fafb`, `#545454`) and the **3px green rule** along the bottom of the outside spread.

---

## Files

| File | Purpose |
|------|--------|
| `spread-outside-5x7-vistaprint.html` | **Outside** with bleed: **back** (left) = 4c logo on light canvas; **front** (right) = reverse logo on dark. |
| `spread-inside-5x7-vistaprint.html` | **Inside** with bleed: **blank white** both panels (handwriting). |
| `signix-outside-svg.html` | **Print-safe outside** — SVG-based version with inline fills; use this for wkhtmltopdf export (see Export section). |
| `signix-inside-svg.html` | **Print-safe inside** — SVG-based blank white; use this for wkhtmltopdf export. |
| `README.md` | Workflow and VistaPrint checklist. |

---

## Print geometry

| Spec | Value |
|------|--------|
| **Folded size** | **5″ × 7″** (portrait). |
| **Each spread (trim)** | **10″ × 7″** flat. |
| **Bleed** | **0.125″** all sides → file **10.25″ × 7.25″**. |
| **Fold** | Vertical center (**5″** from left trim). |

**Outside:** left panel = **back** of card; right = **front** (first thing recipient sees).  
**Inside:** open flat; reps write on either or both panels.

Confirm dimensions against your exact [VistaPrint](https://www.vistaprint.com/) 5×7 folded product before ordering.

---

## VistaPrint checklist

1. Product: **folded** card, **5×7**, matte or premium matte if you want a more executive feel.
2. Upload **outside** and **inside** PDFs **separately** (unless their wizard specifies one multi-page file).
3. PDF page size **10.25″ × 7.25″**; backgrounds print to the bleed edge.
4. Approve the proof: logos stay inside safe margins (HTML already insets content).

---

## Export to PDF

> **Important:** `spread-outside-5x7-vistaprint.html` uses CSS custom properties (`var()`) which wkhtmltopdf 0.12.x does not support — background colors will not render if you point wkhtmltopdf at those files directly. Always use the `signix-*-svg.html` files for wkhtmltopdf exports; they use inline SVG fills that render correctly at any version.

**Option A — wkhtmltopdf (recommended, one command per file):**

```bash
CARD_DIR="/Users/chris/Desktop/AI Summit 2026 Q2/proj-template-and-lease-SIGNiX-app/PROJECT-DOCS/06-DOCS/SIGNiX-EXECUTIVE-GREETING-CARD-VISTAPRINT"

wkhtmltopdf --page-width 10.25in --page-height 7.25in --disable-smart-shrinking \
  --enable-local-file-access --margin-top 0 --margin-right 0 --margin-bottom 0 --margin-left 0 \
  --dpi 300 --print-media-type \
  "$CARD_DIR/signix-outside-svg.html" ~/Desktop/signix-card-outside.pdf

wkhtmltopdf --page-width 10.25in --page-height 7.25in --disable-smart-shrinking \
  --enable-local-file-access --margin-top 0 --margin-right 0 --margin-bottom 0 --margin-left 0 \
  --dpi 300 --print-media-type \
  "$CARD_DIR/signix-inside-svg.html" ~/Desktop/signix-card-inside.pdf
```

Both PDFs land on your Desktop, ready to upload to Vistaprint.

**Option B — Chrome / Edge (fallback):** open each `signix-*-svg.html` file → `Cmd+P` → Save as PDF → Orientation: **Landscape** → Paper: **Custom 10.25 × 7.25 in** → Margins: **None** → ✅ Background graphics → Save.

---

## Revision history

- **2026-04-02** — Added `signix-outside-svg.html` and `signix-inside-svg.html` (SVG-based print-safe variants). Updated export instructions: wkhtmltopdf 0.12.x does not render CSS custom properties as background colors; SVG `<rect>` fills render correctly. README now points to SVG files as the canonical wkhtmltopdf export source.
- **2026-03-27** — Simple fold-over: logo-only outside, blank inside; removed preprinted letter and headshot asset.
- **2026-03-27** — Earlier: executive inside copy and Aspen photo (retired in favor of this simple version).

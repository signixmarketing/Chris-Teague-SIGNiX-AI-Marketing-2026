# Knowledge: HTML-to-PDF for Document Generation

This document describes **how generated HTML is converted to PDF** in document-centric applications—the technology, constraints, and alternatives. This project uses **wkhtmltopdf** (system binary) with **pdfkit** (Python wrapper). Setup steps are in **SETUP-WKHTMLTOPDF.md**; design references are in **DESIGN-DOCS.md**.

---

## 1. Role in Document Generation

The typical flow for **dynamic** document templates is:

1. **Render** — Build HTML from a template (e.g. Django template) and deal data (e.g. `get_deal_data(deal)`).
2. **Convert** — Convert the rendered HTML to PDF using a tool that renders HTML and exports PDF.
3. **Store** — Save the PDF (e.g. as a `DocumentInstanceVersion` file or in a document repository).

HTML-to-PDF is step 2. It must support the same HTML/CSS that the template produces (including images loaded via URL, fonts, and layout) so that the PDF matches what the user would see in a browser.

---

## 2. wkhtmltopdf and pdfkit

- **wkhtmltopdf** — Command-line tool that uses **WebKit** to render HTML and output PDF. It must be installed on the **system** (not via pip). Available for Linux, macOS, and Windows; open source. [wkhtmltopdf.org](https://wkhtmltopdf.org/).
- **pdfkit** — Python package that invokes the `wkhtmltopdf` binary. Install via `pip install pdfkit`. The application passes HTML (string or URL) and options to pdfkit; pdfkit runs the binary and returns the PDF bytes.

**Why this stack:** Used in an earlier prototype and works well for Django-rendered HTML. Alternatives (WeasyPrint, headless Chrome) are viable; see Section 5.

---

## 3. Constraints and Gotchas

### 3.1 Image URLs must be absolute

wkhtmltopdf fetches images (and other resources) from the HTML. If the HTML contains **relative** URLs (e.g. `src="/media/images/logo.png"`), the tool may not resolve them correctly because it has no "current page" base URL in some environments.

- **Solution:** Use **absolute** URLs for all images in the HTML passed to wkhtmltopdf (e.g. `http://localhost:8000/media/images/logo.png` or `https://your-app.example.com/media/images/logo.png`).
- **In this app:** The context builder uses `request.build_absolute_uri(image.file.url)` when building the template context for document generation (so the template receives a full URL). When there is no request (e.g. management command), the app uses `settings.SITE_URL` + relative path; SITE_URL must be set for image loading to work in that case. See DESIGN-DOCS and SETUP-WKHTMLTOPDF.

### 3.2 Do not use `--base-url`

Many system builds of wkhtmltopdf (e.g. **0.12.6**) do **not** support the `--base-url` option and exit with "Unknown long argument --base-url". This project **does not** pass `--base-url`; instead, image URLs in the HTML are built as absolute URLs before conversion. See SETUP-WKHTMLTOPDF Section 6.

### 3.3 System dependency

wkhtmltopdf is a **system** binary. It must be installed separately (apt, brew, or Windows installer). The Python environment only needs pdfkit; pdfkit calls the binary. So setup has two parts: (1) install wkhtmltopdf on the system, (2) ensure pdfkit is installed and can find the binary. SETUP-WKHTMLTOPDF covers both.

### 3.4 Availability check

This application registers a Django system check (e.g. `documents.W001`) that warns when wkhtmltopdf is missing. Before running document generation, the app calls `check_wkhtmltopdf_available()` and raises a clear error with install hints if the binary is not on PATH. That avoids opaque failures when generating PDFs.

---

## 4. How This App Uses It

| Component | Role |
|-----------|------|
| **wkhtmltopdf** | System binary; must be on PATH. Invoked by pdfkit. |
| **pdfkit** | Python package; in `requirements.txt`. Wraps the binary. |
| **apps.documents.services** | `check_wkhtmltopdf_available()`, `_require_wkhtmltopdf()`, `render_dynamic_template_to_pdf()`. Renders HTML from template + context, then calls pdfkit to produce PDF bytes. |
| **apps.documents.checks** | Django check `documents.W001`: warns when wkhtmltopdf is missing. |

Dynamic templates are rendered to HTML (Django template + deal data + image URLs); that HTML is passed to pdfkit; the resulting PDF is stored in a `DocumentInstanceVersion`. Without wkhtmltopdf, dynamic document generation fails with `DocumentGenerationError`. See DESIGN-DOCS.md and PLAN-ADD-DOCUMENT-SETS.

---

## 5. Alternatives

- **WeasyPrint** — Python library; uses different rendering engine. Can be a drop-in alternative if you prefer a pure-Python stack (no system binary). Layout and CSS support differ from WebKit.
- **Headless Chrome / Puppeteer / Playwright** — Render HTML in a headless browser and export PDF. Good fidelity to browser rendering; heavier dependency (browser binary).
- **Other cloud or API services** — Various SaaS offerings for HTML-to-PDF. Offload conversion; require network and possibly credentials.

If you switch technology, the **contract** remains: the document generation layer needs a function that accepts (HTML string or URL, options) and returns PDF bytes. Only the implementation of that function changes. DESIGN-DOCS does not mandate wkhtmltopdf forever; it specifies the pipeline (render HTML → convert to PDF → store). See DESIGN-DOCS and SETUP-WKHTMLTOPDF for references.

---

## 6. References in This Repo

| Document | Content |
|----------|---------|
| **SETUP-WKHTMLTOPDF.md** | Step-by-step setup: check if installed, install binary, install pdfkit, verify. Run after PLAN-MASTER plans 1–4, before PLAN-DOCS-MASTER. |
| **DESIGN-DOCS.md** | Dynamic template → HTML → PDF (pdfkit/wkhtmltopdf); image URL handling; document generation flow. |
| **PLAN-ADD-DOCUMENT-SETS.md** | Implementation of document generation; pdfkit and wkhtmltopdf in context. |
| **PLAN-MASTER.md** | Setup: wkhtmltopdf after plans 1–4, before Document Features. |

---

*This knowledge file describes **HTML-to-PDF** for document generation. For setup steps, see **SETUP-WKHTMLTOPDF.md**. For design decisions, see **DESIGN-DOCS.md**.*
